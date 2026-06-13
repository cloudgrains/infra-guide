"""
Local web command center for infra-guide.
"""

import contextlib
import io
import json
import os
import shlex
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from infra_guide import __version__
from infra_guide.guides import apply, destroy, init, plan
from infra_guide.preferences import THEMES, get_web_theme_palette

GUIDE_MODULES = {
    "init": init,
    "plan": plan,
    "apply": apply,
    "destroy": destroy,
}

RUNNER_COMMANDS = [
    {
        "name": "init",
        "description": "Initialize providers, modules, and backend settings.",
        "risk": "low",
        "example": "--upgrade",
    },
    {
        "name": "plan",
        "description": "Preview infrastructure changes and optionally save a plan file.",
        "risk": "low",
        "example": "--out tfplan",
    },
    {
        "name": "apply",
        "description": "Apply infrastructure changes with cost insight before execution.",
        "risk": "medium",
        "example": "--plan-file tfplan",
    },
    {
        "name": "destroy",
        "description": "Destroy managed infrastructure from the current workspace.",
        "risk": "high",
        "example": "--target aws_instance.temporary",
    },
    {
        "name": "fmt",
        "description": "Format Terraform/OpenTofu files across the current workspace.",
        "risk": "low",
        "example": "--check --diff",
    },
]

RUNNER_COMMAND_NAMES = {item["name"] for item in RUNNER_COMMANDS}

ACTION_COMMANDS = [
    {
        "name": "doctor",
        "description": "Run workspace diagnostics and pre-flight checks.",
        "risk": "low",
        "args": "",
    },
    {
        "name": "doctor",
        "description": "Run diagnostics plus drift detection.",
        "risk": "low",
        "args": "--with-drift",
        "label": "doctor + drift",
    },
    {
        "name": "validate",
        "description": "Check configuration, formatting, backend, and variables.",
        "risk": "low",
        "args": "",
    },
    {
        "name": "drift",
        "description": "Detect infrastructure drift from refresh-only planning.",
        "risk": "low",
        "args": "",
    },
    {
        "name": "cicd",
        "description": "Run init, validation, and plan in a pipeline-style flow.",
        "risk": "medium",
        "args": "",
    },
]


class WebCommandCenterBackend:
    """Expose infra-guide features to a local browser UI."""

    def __init__(
        self,
        tool_name: str,
        tool_version: str,
        services: Dict[str, Any],
        theme_name: Optional[str] = None,
    ):
        self.tool_name = tool_name
        self.tool_version = tool_version
        self.services = services
        self.theme_name = theme_name or services["preferences"].get_theme_name()
        self.execution_lock = threading.Lock()

    def get_context(self) -> Dict[str, Any]:
        """Return the full page context for the web UI."""
        return {
            "app": {
                "name": "infra-guide",
                "version": __version__,
                "tool_name": self.tool_name,
                "tool_version": self.tool_version,
                "cwd": os.getcwd(),
            },
            "theme_name": self.theme_name,
            "themes": self._serialize_themes(),
            "snapshot": self.services["inspector"].inspect(include_state=False),
            "runner_commands": RUNNER_COMMANDS,
            "action_commands": ACTION_COMMANDS,
            "guides": self._serialize_guides(),
            "history": [
                self._serialize_saved_entry(entry)
                for entry in self.services["preferences"].get_history(limit=8)
            ],
            "favorites": [
                self._serialize_saved_entry(entry)
                for entry in self.services["preferences"].get_favorites()
            ],
            "state": self.get_state_overview(),
            "workspaces": self.services["workspace_manager"].list_workspaces(),
        }

    def get_state_overview(self, limit: int = 18) -> Dict[str, Any]:
        """Return state stats and a sample of resources."""
        explorer = self.services["state_explorer"]
        resources = explorer.list_resources()
        stats = explorer.get_state_stats()
        return {
            "stats": stats,
            "resources": resources[:limit],
            "truncated": len(resources) > limit,
            "resource_count": len(resources),
        }

    def get_state_detail(self, resource_address: str) -> Dict[str, Any]:
        """Return detail for one state resource."""
        detail = self.services["state_explorer"].show_resource_detail(resource_address)
        if not detail:
            return {
                "success": False,
                "address": resource_address,
                "detail": "",
                "error": "Could not load resource detail from the current state.",
            }
        return {
            "success": True,
            "address": resource_address,
            "detail": detail,
        }

    def set_theme(self, theme_name: str) -> Dict[str, Any]:
        """Persist and activate a theme."""
        if theme_name not in THEMES:
            return {"success": False, "error": "Unknown theme."}
        self.services["preferences"].set_theme(theme_name)
        self.theme_name = theme_name
        return {
            "success": True,
            "theme_name": theme_name,
            "palette": get_web_theme_palette(theme_name),
        }

    def clear_history(self) -> Dict[str, Any]:
        """Remove stored command history."""
        self.services["preferences"].clear_history()
        return {"success": True}

    def toggle_favorite(self, command_name: str, raw_args: str = "") -> Dict[str, Any]:
        """Toggle a runner command favorite."""
        if command_name not in RUNNER_COMMAND_NAMES:
            return {
                "success": False,
                "error": "Only execution commands can be favorited in the web UI.",
            }

        ok, args, error = self._split_args(raw_args)
        if not ok:
            return {"success": False, "error": error}

        preview = self.services["runner"].format_command(command_name, args)
        enabled = self.services["preferences"].toggle_favorite(command_name, args, preview)
        return {
            "success": True,
            "enabled": enabled,
            "preview": preview,
        }

    def run_workspace_action(self, action: str, name: str = "") -> Dict[str, Any]:
        """Create, select, delete, or list workspaces."""
        manager = self.services["workspace_manager"]

        if action == "list":
            return manager.list_workspaces()
        if action == "create":
            result = manager.create_workspace(name)
        elif action == "select":
            result = manager.select_workspace(name)
        elif action == "delete":
            result = manager.delete_workspace(name)
        else:
            return {"success": False, "error": "Unsupported workspace action."}

        payload = {
            "success": result.get("success", False),
            "exit_code": result.get("exit_code"),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "workspaces": manager.list_workspaces(),
        }
        return payload

    def run_command(
        self, command_name: str, raw_args: str = "", confirm_execution: bool = False
    ) -> Dict[str, Any]:
        """Run a command or action from the browser."""
        ok, args, error = self._split_args(raw_args)
        if not ok:
            return self._error_result(command_name, raw_args, error, exit_code=2)

        if command_name in RUNNER_COMMAND_NAMES:
            normalized_ok, normalized_args, normalize_error = self._normalize_runner_args(
                command_name, args
            )
            if not normalized_ok:
                return self._error_result(command_name, raw_args, normalize_error, exit_code=2)
            return self._run_runner_command(command_name, normalized_args, confirm_execution)
        if command_name == "doctor":
            return self._run_doctor(args)
        if command_name == "validate":
            return self._run_validate()
        if command_name == "drift":
            return self._run_drift()
        if command_name == "cicd":
            return self._run_cicd(args)

        return self._error_result(
            command_name,
            raw_args,
            "Unsupported command for the web command center.",
            exit_code=2,
        )

    def read_logo(self) -> bytes:
        """Load the packaged logo bytes."""
        with resources.open_binary("infra_guide.assets", "infra-guide.png") as handle:
            return handle.read()

    def _run_runner_command(
        self, command_name: str, args: List[str], confirm_execution: bool
    ) -> Dict[str, Any]:
        final_args = list(args)
        if command_name in ("apply", "destroy") and "-auto-approve" not in final_args:
            if not confirm_execution:
                return self._error_result(
                    command_name,
                    self._stringify_args(args),
                    (
                        "This action needs explicit confirmation in the browser. "
                        "Enable the confirmation toggle to continue."
                    ),
                    exit_code=2,
                )
            final_args.append("-auto-approve")

        preview = self.services["runner"].format_command(command_name, final_args)
        cost_preview = None
        if command_name == "apply":
            cost_preview = self.services["cost_estimator"].estimate_apply_cost(final_args)

        if not self.execution_lock.acquire(blocking=False):
            return self._error_result(
                command_name,
                self._stringify_args(final_args),
                "Another command is already running in the web command center.",
                exit_code=409,
            )

        try:
            result = self.services["runner"].execute_capture(command_name, final_args)
        finally:
            self.execution_lock.release()

        detailed_exitcode = command_name == "plan" and "-detailed-exitcode" in final_args
        success = result["exit_code"] == 0 or (detailed_exitcode and result["exit_code"] == 2)

        self.services["preferences"].record_execution(
            command_name,
            final_args,
            preview,
            os.getcwd(),
            result["exit_code"],
        )

        return {
            "kind": "runner",
            "success": success,
            "exit_code": result["exit_code"],
            "command_name": command_name,
            "args": final_args,
            "preview": preview,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "duration_seconds": result["duration_seconds"],
            "summary": self._summarize_runner_result(
                command_name, result["exit_code"], detailed_exitcode
            ),
            "cost_preview": cost_preview,
        }

    def _run_doctor(self, args: List[str]) -> Dict[str, Any]:
        with_drift = "--with-drift" in args
        snapshot = self.services["inspector"].inspect(include_state=True)
        validation = self.services["validator"].run_all_checks()
        drift = None
        exit_code = 1 if validation["failed"] > 0 else 0

        if with_drift:
            drift = self.services["drift_detector"].detect_drift()
            if not drift.get("success"):
                exit_code = 1

        return {
            "kind": "doctor",
            "success": exit_code == 0,
            "exit_code": exit_code,
            "preview": self._join_command(["infra-guide", "doctor"] + args),
            "snapshot": snapshot,
            "validation": validation,
            "drift": drift,
        }

    def _run_validate(self) -> Dict[str, Any]:
        validation = self.services["validator"].run_all_checks()
        return {
            "kind": "validation",
            "success": validation["failed"] == 0,
            "exit_code": 0 if validation["failed"] == 0 else 1,
            "preview": "infra-guide validate",
            "validation": validation,
        }

    def _run_drift(self) -> Dict[str, Any]:
        drift = self.services["drift_detector"].detect_drift()
        exit_code = 1
        if drift.get("success"):
            exit_code = 2 if drift.get("drift_detected") else 0
        return {
            "kind": "drift",
            "success": drift.get("success", False),
            "exit_code": exit_code,
            "preview": "infra-guide drift",
            "drift": drift,
        }

    def _run_cicd(self, args: List[str]) -> Dict[str, Any]:
        skip_init = "--skip-init" in args
        skip_validation = "--skip-validation" in args
        output_file = "tfplan"
        for value in args:
            if value.startswith("--out="):
                output_file = value.split("=", 1)[1].strip() or "tfplan"

        pipeline = self.services["cicd_runner"].run_pipeline_capture(
            skip_init=skip_init,
            skip_validation=skip_validation,
            output_file=output_file,
        )
        return {
            "kind": "cicd",
            "success": pipeline["success"],
            "exit_code": 0 if pipeline["success"] else 1,
            "preview": self._join_command(["infra-guide", "cicd"] + args),
            "pipeline": pipeline,
        }

    def _serialize_themes(self) -> List[Dict[str, Any]]:
        themes = []
        for name, data in THEMES.items():
            themes.append(
                {
                    "name": name,
                    "label": data["label"],
                    "description": data["description"],
                    "palette": get_web_theme_palette(name),
                }
            )
        return themes

    def _serialize_guides(self) -> Dict[str, Dict[str, Any]]:
        guides = {}
        for name, module in GUIDE_MODULES.items():
            guide = module.get_guide()
            guides[name] = {
                "description": guide["description"],
                "flags": guide["flags"],
                "warnings": guide["warnings"],
                "best_practices": guide["best_practices"],
                "examples": guide.get("examples", []),
                "risk": guide.get("risk", "low"),
            }
        return guides

    def _serialize_saved_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(entry)
        payload["raw_args"] = self._join_command(list(entry.get("args", [])))
        return payload

    def _summarize_runner_result(
        self, command_name: str, exit_code: int, detailed_exitcode: bool
    ) -> str:
        if command_name == "plan" and detailed_exitcode and exit_code == 2:
            return "Plan completed and detected infrastructure changes."
        if exit_code == 0:
            return "{0} completed successfully.".format(command_name)
        return "{0} exited with code {1}.".format(command_name, exit_code)

    def _split_args(self, raw_args: str) -> Tuple[bool, List[str], str]:
        try:
            return True, shlex.split(raw_args or ""), ""
        except ValueError as error:
            return False, [], str(error)

    def _normalize_runner_args(
        self, command_name: str, args: List[str]
    ) -> Tuple[bool, List[str], str]:
        from infra_guide.cli import build_command_args, build_fmt_args, build_parser

        parser = build_parser()
        stderr_buffer = io.StringIO()

        try:
            with contextlib.redirect_stderr(stderr_buffer):
                parsed = parser.parse_args([command_name] + args)
        except SystemExit:
            error = stderr_buffer.getvalue().strip() or "Could not parse command arguments."
            return False, [], error

        if command_name == "fmt":
            return True, build_fmt_args(parsed), ""
        return True, build_command_args(command_name, parsed), ""

    def _stringify_args(self, args: List[str]) -> str:
        if not args:
            return ""
        return self._join_command(args)

    def _join_command(self, parts: List[str]) -> str:
        try:
            return shlex.join(parts)
        except AttributeError:
            return " ".join(shlex.quote(part) for part in parts)

    def _error_result(
        self, command_name: str, raw_args: str, error: str, exit_code: int = 1
    ) -> Dict[str, Any]:
        preview_parts = ["infra-guide", command_name]
        if raw_args:
            ok, args, _ = self._split_args(raw_args)
            if ok:
                preview_parts.extend(args)
        return {
            "kind": "error",
            "success": False,
            "exit_code": exit_code,
            "command_name": command_name,
            "preview": self._join_command(preview_parts),
            "error": error,
        }


class WebCommandCenter:
    """Host the local web application."""

    def __init__(
        self,
        tool_name: str,
        tool_version: str,
        services: Dict[str, Any],
        host: str = "127.0.0.1",
        port: int = 8765,
        open_browser: bool = True,
        theme_name: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.open_browser = open_browser
        self.backend = WebCommandCenterBackend(
            tool_name=tool_name,
            tool_version=tool_version,
            services=services,
            theme_name=theme_name,
        )

    def serve(self) -> int:
        """Start the local server and block until interrupted."""
        handler = self._build_handler()
        server = ThreadingHTTPServer((self.host, self.port), handler)
        actual_port = server.server_address[1]
        open_host = "127.0.0.1" if self.host in ("0.0.0.0", "") else self.host
        url = "http://{0}:{1}".format(open_host, actual_port)
        print("infra-guide web is running at {0}".format(url))
        print("Press Ctrl+C to stop the local web command center.")

        if self.open_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping infra-guide web.")
        finally:
            server.server_close()
        return 0

    def _build_handler(self):
        backend = self.backend

        class RequestHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                if parsed.path == "/":
                    self._send_html(APP_HTML)
                    return
                if parsed.path == "/api/context":
                    self._send_json(200, backend.get_context())
                    return
                if parsed.path == "/api/state/detail":
                    query = parse_qs(parsed.query)
                    address = query.get("address", [""])[0].strip()
                    if not address:
                        self._send_json(
                            400, {"success": False, "error": "Missing resource address."}
                        )
                        return
                    self._send_json(200, backend.get_state_detail(address))
                    return
                if parsed.path == "/assets/logo":
                    self._send_binary("image/png", backend.read_logo())
                    return

                self._send_json(404, {"success": False, "error": "Not found."})

            def do_POST(self) -> None:
                payload = self._read_json_body()
                if payload is None:
                    self._send_json(400, {"success": False, "error": "Invalid JSON body."})
                    return

                if self.path == "/api/run":
                    result = backend.run_command(
                        command_name=str(payload.get("command_name", "")).strip(),
                        raw_args=str(payload.get("raw_args", "")),
                        confirm_execution=bool(payload.get("confirm_execution", False)),
                    )
                    self._send_json(200, result)
                    return

                if self.path == "/api/theme":
                    result = backend.set_theme(str(payload.get("theme_name", "")).strip())
                    self._send_json(200 if result.get("success") else 400, result)
                    return

                if self.path == "/api/history/clear":
                    self._send_json(200, backend.clear_history())
                    return

                if self.path == "/api/favorite/toggle":
                    result = backend.toggle_favorite(
                        command_name=str(payload.get("command_name", "")).strip(),
                        raw_args=str(payload.get("raw_args", "")),
                    )
                    self._send_json(200 if result.get("success") else 400, result)
                    return

                if self.path == "/api/workspace":
                    result = backend.run_workspace_action(
                        action=str(payload.get("action", "")).strip(),
                        name=str(payload.get("name", "")).strip(),
                    )
                    self._send_json(200 if result.get("success") else 400, result)
                    return

                self._send_json(404, {"success": False, "error": "Not found."})

            def _read_json_body(self) -> Optional[Dict[str, Any]]:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length <= 0:
                    return {}
                try:
                    raw_body = self.rfile.read(content_length).decode("utf-8")
                    return json.loads(raw_body)
                except Exception:
                    return None

            def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def _send_html(self, body: str) -> None:
                encoded = body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(encoded)

            def _send_binary(self, content_type: str, body: bytes) -> None:
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(body)

        return RequestHandler


APP_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>infra-guide web</title>
  <style>
    :root {
      --bg: #06131d;
      --bg-alt: #0a1826;
      --surface: #102438;
      --surface-alt: #15314a;
      --border: #1e7db4;
      --text: #f4fbff;
      --muted: #8ea8b6;
      --brand: #35d9ff;
      --accent: #00c2ff;
      --accent-alt: #ff61d2;
      --success: #22c55e;
      --warning: #f59e0b;
      --danger: #ef4444;
      --chip-bg: #163042;
      --shadow: rgba(0, 0, 0, 0.24);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, color-mix(in srgb, var(--accent) 18%, transparent), transparent 22%),
        radial-gradient(circle at right top, color-mix(in srgb, var(--accent-alt) 18%, transparent), transparent 20%),
        linear-gradient(180deg, var(--bg-alt), var(--bg));
    }

    a {
      color: inherit;
    }

    .shell {
      width: min(1440px, calc(100vw - 32px));
      margin: 20px auto 32px;
    }

    .hero {
      display: grid;
      grid-template-columns: 180px 1fr;
      gap: 24px;
      padding: 24px;
      border: 1px solid color-mix(in srgb, var(--border) 60%, transparent);
      border-radius: 28px;
      background:
        linear-gradient(180deg, color-mix(in srgb, var(--surface) 92%, transparent), color-mix(in srgb, var(--surface-alt) 90%, transparent));
      box-shadow: 0 20px 60px var(--shadow);
      backdrop-filter: blur(16px);
    }

    .hero-logo {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 148px;
      border-radius: 22px;
      border: 1px solid color-mix(in srgb, var(--border) 55%, transparent);
      background: linear-gradient(160deg, color-mix(in srgb, var(--chip-bg) 80%, transparent), color-mix(in srgb, var(--surface-alt) 92%, transparent));
    }

    .hero-logo img {
      width: 120px;
      max-width: 100%;
      height: auto;
      display: block;
    }

    .hero-copy h1 {
      margin: 0;
      font-size: clamp(2.1rem, 4vw, 3.4rem);
      letter-spacing: -0.04em;
      line-height: 0.95;
    }

    .hero-copy p {
      margin: 10px 0 0;
      max-width: 820px;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.5;
    }

    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      padding: 8px 12px;
      border: 1px solid color-mix(in srgb, var(--border) 45%, transparent);
      background: color-mix(in srgb, var(--chip-bg) 84%, transparent);
      color: var(--text);
      font-size: 0.92rem;
    }

    .chip strong {
      color: var(--brand);
      font-weight: 700;
    }

    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 18px;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.9fr);
      gap: 18px;
      margin-top: 18px;
    }

    .stack {
      display: grid;
      gap: 18px;
    }

    .card {
      border-radius: 24px;
      border: 1px solid color-mix(in srgb, var(--border) 45%, transparent);
      background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 94%, transparent), color-mix(in srgb, var(--surface-alt) 86%, transparent));
      box-shadow: 0 18px 48px rgba(0, 0, 0, 0.18);
      padding: 20px;
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }

    .card h2,
    .card h3 {
      margin: 0;
      font-size: 1rem;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      color: var(--brand);
    }

    .subtle {
      color: var(--muted);
      font-size: 0.92rem;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }

    .stat {
      padding: 16px;
      border-radius: 18px;
      background: color-mix(in srgb, var(--surface-alt) 90%, transparent);
      border: 1px solid color-mix(in srgb, var(--border) 35%, transparent);
    }

    .stat label {
      display: block;
      color: var(--muted);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .stat strong {
      display: block;
      margin-top: 8px;
      font-size: 1.3rem;
    }

    .quick-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 12px;
    }

    .action-card {
      text-align: left;
      padding: 14px;
      border-radius: 18px;
      border: 1px solid color-mix(in srgb, var(--border) 40%, transparent);
      background: color-mix(in srgb, var(--surface-alt) 88%, transparent);
    }

    .action-card strong {
      display: block;
      margin-bottom: 8px;
      font-size: 1rem;
    }

    .action-card small {
      color: var(--muted);
      display: block;
      min-height: 44px;
      line-height: 1.35;
    }

    .risk {
      display: inline-flex;
      margin-top: 10px;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      background: color-mix(in srgb, var(--chip-bg) 82%, transparent);
      border: 1px solid color-mix(in srgb, var(--border) 30%, transparent);
    }

    .form-grid {
      display: grid;
      grid-template-columns: 220px 1fr 160px;
      gap: 12px;
      align-items: end;
    }

    label span {
      display: block;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    input,
    select,
    button,
    textarea {
      width: 100%;
      border: 1px solid color-mix(in srgb, var(--border) 45%, transparent);
      background: color-mix(in srgb, var(--bg) 58%, transparent);
      color: var(--text);
      border-radius: 16px;
      padding: 12px 14px;
      font: inherit;
      outline: none;
    }

    textarea {
      min-height: 92px;
      resize: vertical;
    }

    input:focus,
    select:focus,
    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent);
    }

    button {
      cursor: pointer;
      font-weight: 700;
      transition: transform 140ms ease, background 140ms ease, border-color 140ms ease;
    }

    button:hover {
      transform: translateY(-1px);
    }

    .primary {
      background: linear-gradient(135deg, color-mix(in srgb, var(--accent) 92%, black 8%), color-mix(in srgb, var(--brand) 88%, black 12%));
      color: #04131d;
      border-color: transparent;
    }

    .secondary {
      background: color-mix(in srgb, var(--surface-alt) 92%, transparent);
    }

    .danger {
      border-color: color-mix(in srgb, var(--danger) 45%, transparent);
      color: color-mix(in srgb, var(--danger) 86%, white 14%);
    }

    .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }

    .button-row button {
      width: auto;
      min-width: 140px;
    }

    .note {
      margin-top: 12px;
      padding: 12px 14px;
      border-radius: 16px;
      background: color-mix(in srgb, var(--chip-bg) 76%, transparent);
      color: var(--muted);
      line-height: 1.45;
    }

    .list {
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }

    .list-item {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      padding: 12px 14px;
      border-radius: 16px;
      background: color-mix(in srgb, var(--surface-alt) 86%, transparent);
      border: 1px solid color-mix(in srgb, var(--border) 32%, transparent);
      align-items: center;
    }

    .list-item strong {
      display: block;
      margin-bottom: 4px;
      font-size: 0.95rem;
    }

    .list-item small {
      display: block;
      color: var(--muted);
      line-height: 1.35;
    }

    .mini-actions {
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .mini-actions button {
      width: auto;
      padding: 8px 10px;
      border-radius: 12px;
      font-size: 0.84rem;
    }

    .guide {
      display: grid;
      gap: 12px;
    }

    .guide-block {
      padding: 14px;
      border-radius: 16px;
      background: color-mix(in srgb, var(--surface-alt) 86%, transparent);
      border: 1px solid color-mix(in srgb, var(--border) 28%, transparent);
    }

    .guide-block ul {
      padding-left: 18px;
      margin: 10px 0 0;
    }

    .guide-block li {
      margin: 6px 0;
      color: var(--muted);
    }

    .terminal {
      min-height: 240px;
      border-radius: 18px;
      overflow: hidden;
      border: 1px solid color-mix(in srgb, var(--border) 30%, transparent);
      background: linear-gradient(180deg, rgba(3, 8, 14, 0.94), rgba(6, 12, 18, 0.98));
    }

    .terminal-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      border-bottom: 1px solid color-mix(in srgb, var(--border) 26%, transparent);
      background: color-mix(in srgb, var(--surface) 70%, transparent);
      font-size: 0.9rem;
      color: var(--muted);
    }

    .terminal-body {
      padding: 16px;
    }

    .terminal-body pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
      font-size: 0.92rem;
      line-height: 1.55;
      color: #d9f7ff;
    }

    .terminal-block + .terminal-block {
      margin-top: 14px;
      padding-top: 14px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
    }

    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 0.84rem;
      background: color-mix(in srgb, var(--chip-bg) 84%, transparent);
      border: 1px solid color-mix(in srgb, var(--border) 28%, transparent);
    }

    .status-ready {
      color: var(--success);
    }

    .status-warning {
      color: var(--warning);
    }

    .status-danger {
      color: var(--danger);
    }

    .workspace-row {
      display: grid;
      grid-template-columns: 1fr auto auto auto;
      gap: 10px;
      align-items: center;
      margin-top: 12px;
    }

    .muted-link {
      color: var(--muted);
      text-decoration: none;
    }

    .footer-note {
      margin-top: 16px;
      font-size: 0.9rem;
      color: var(--muted);
    }

    @media (max-width: 1100px) {
      .layout,
      .hero {
        grid-template-columns: 1fr;
      }

      .quick-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .stats-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .form-grid,
      .workspace-row {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 720px) {
      .shell {
        width: min(100vw - 18px, 1440px);
        margin: 10px auto 24px;
      }

      .hero,
      .card {
        padding: 16px;
      }

      .quick-grid,
      .stats-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="hero-logo">
        <img src="/assets/logo" alt="infra-guide logo">
      </div>
      <div class="hero-copy">
        <h1>infra-guide web</h1>
        <p>Local browser command center for Terraform and OpenTofu. Same workspace, same guidance, same command history and favorites, but in a cleaner web UI on localhost.</p>
        <div class="chips" id="hero-chips"></div>
        <div class="hero-actions">
          <label style="min-width: 240px;">
            <span>Theme</span>
            <select id="theme-select"></select>
          </label>
          <button class="secondary" id="refresh-context">Refresh Dashboard</button>
          <button class="secondary" id="clear-history">Clear History</button>
        </div>
      </div>
    </section>

    <div class="layout">
      <main class="stack">
        <section class="card">
          <div class="card-header">
            <h2>Workspace Snapshot</h2>
            <span class="subtle" id="workspace-path"></span>
          </div>
          <div class="stats-grid" id="stats-grid"></div>
          <div class="note" id="recommendation-note"></div>
        </section>

        <section class="card">
          <div class="card-header">
            <h2>Quick Actions</h2>
            <span class="subtle">Diagnostics and pipeline-safe flows</span>
          </div>
          <div class="quick-grid" id="quick-actions"></div>
        </section>

        <section class="card">
          <div class="card-header">
            <h2>Runner</h2>
            <span class="subtle">Real local execution with captured terminal output</span>
          </div>
          <div class="form-grid">
            <label>
              <span>Command</span>
              <select id="command-select"></select>
            </label>
            <label>
              <span>Args</span>
              <input id="args-input" type="text" placeholder="--out tfplan or --check --diff">
            </label>
            <label>
              <span>Safety</span>
              <select id="confirm-select">
                <option value="false">Normal</option>
                <option value="true">Confirm apply/destroy</option>
              </select>
            </label>
          </div>
          <div class="button-row">
            <button class="primary" id="run-command">Run Command</button>
            <button class="secondary" id="favorite-command">Toggle Favorite</button>
            <button class="secondary" id="load-example">Load Example</button>
          </div>
          <div class="note">Runner args use the same syntax as <code>infra-guide</code> on the CLI. For raw tool passthrough flags, add them after <code>--</code>. Apply and destroy are browser-confirmed and will automatically add <code>-auto-approve</code> so the local tool can run non-interactively.</div>
        </section>

        <section class="card">
          <div class="card-header">
            <h2>Guide</h2>
            <span class="subtle" id="guide-risk"></span>
          </div>
          <div class="guide" id="guide-panel"></div>
        </section>

        <section class="card">
          <div class="card-header">
            <h2>Terminal Output</h2>
            <span class="subtle" id="result-status">Waiting for a command</span>
          </div>
          <div class="terminal" id="terminal-panel">
            <div class="terminal-head">
              <span id="terminal-command">No command yet</span>
              <span id="terminal-meta">Local execution</span>
            </div>
            <div class="terminal-body" id="terminal-body"></div>
          </div>
        </section>
      </main>

      <aside class="stack">
        <section class="card">
          <div class="card-header">
            <h3>Recent Commands</h3>
            <span class="subtle">Shared with the TUI</span>
          </div>
          <div class="list" id="history-list"></div>
        </section>

        <section class="card">
          <div class="card-header">
            <h3>Favorites</h3>
            <span class="subtle">Fast reruns for repeat workflows</span>
          </div>
          <div class="list" id="favorites-list"></div>
        </section>

        <section class="card">
          <div class="card-header">
            <h3>State Explorer</h3>
            <span class="subtle">Read-only state visibility from the browser</span>
          </div>
          <div class="pill-row" id="state-pills"></div>
          <div class="list" id="state-list"></div>
          <label style="margin-top: 12px;">
            <span>Resource Detail</span>
            <input id="state-detail-input" type="text" placeholder="aws_instance.web">
          </label>
          <div class="button-row">
            <button class="secondary" id="state-detail-button">Show Resource Detail</button>
          </div>
        </section>

        <section class="card">
          <div class="card-header">
            <h3>Workspaces</h3>
            <span class="subtle">Create, switch, and delete from the same local project</span>
          </div>
          <div class="list" id="workspace-list"></div>
          <div class="workspace-row">
            <input id="workspace-input" type="text" placeholder="workspace name">
            <button class="secondary" data-workspace-action="create">Create</button>
            <button class="secondary" data-workspace-action="select">Select</button>
            <button class="danger" data-workspace-action="delete">Delete</button>
          </div>
          <div class="footer-note">The current workspace is highlighted. Delete is blocked by the underlying tool when it targets the active workspace.</div>
        </section>
      </aside>
    </div>
  </div>

  <script>
    const appState = {
      context: null,
      lastResult: null
    };

    function escapeHtml(value) {
      return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Request failed");
      }
      return payload;
    }

    function applyTheme(themeName) {
      if (!appState.context) {
        return;
      }
      const theme = appState.context.themes.find((entry) => entry.name === themeName);
      if (!theme) {
        return;
      }
      const palette = theme.palette;
      Object.entries({
        "--bg": palette.bg,
        "--bg-alt": palette.bg_alt,
        "--surface": palette.surface,
        "--surface-alt": palette.surface_alt,
        "--border": palette.border,
        "--text": palette.text,
        "--muted": palette.muted,
        "--brand": palette.brand,
        "--accent": palette.accent,
        "--accent-alt": palette.accent_alt,
        "--success": palette.success,
        "--warning": palette.warning,
        "--danger": palette.danger,
        "--chip-bg": palette.chip_bg
      }).forEach(([key, value]) => {
        document.documentElement.style.setProperty(key, value);
      });
      document.getElementById("theme-select").value = themeName;
    }

    function renderHero(context) {
      const snapshot = context.snapshot;
      const chips = [
        ["Tool", `${context.app.tool_name} (${context.app.tool_version})`],
        ["Workspace", snapshot.workspace],
        ["Readiness", snapshot.readiness_label],
        ["Version", `v${context.app.version}`]
      ];
      document.getElementById("hero-chips").innerHTML = chips
        .map(([label, value]) => `<div class="chip"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value)}</span></div>`)
        .join("");
      document.getElementById("workspace-path").textContent = context.app.cwd;
      document.getElementById("recommendation-note").textContent = snapshot.recommendation;
    }

    function renderStats(context) {
      const snapshot = context.snapshot;
      const stats = [
        ["Readiness", snapshot.readiness_label],
        ["Config Files", String(snapshot.tf_file_count)],
        ["Var Files", String(snapshot.tfvars_file_count)],
        ["Modules", String(snapshot.module_block_count)],
        ["Backend", snapshot.backend_configured ? "Configured" : "Local only"],
        ["Lock File", snapshot.lock_file_present ? "Present" : "Missing"],
        ["State", snapshot.state_present === true ? "Detected" : (snapshot.state_present === false ? "Missing" : "Unknown")],
        ["Workspace", snapshot.workspace]
      ];
      document.getElementById("stats-grid").innerHTML = stats
        .map(([label, value]) => `
          <div class="stat">
            <label>${escapeHtml(label)}</label>
            <strong>${escapeHtml(value)}</strong>
          </div>
        `)
        .join("");
    }

    function renderThemeOptions(context) {
      const select = document.getElementById("theme-select");
      select.innerHTML = context.themes
        .map((theme) => `<option value="${escapeHtml(theme.name)}">${escapeHtml(theme.label)}</option>`)
        .join("");
      applyTheme(context.theme_name);
    }

    function renderQuickActions(context) {
      const grid = document.getElementById("quick-actions");
      grid.innerHTML = context.action_commands
        .map((action) => `
          <button class="action-card secondary" data-action-command="${escapeHtml(action.name)}" data-action-args="${escapeHtml(action.args || "")}">
            <strong>${escapeHtml(action.label || action.name)}</strong>
            <small>${escapeHtml(action.description)}</small>
            <span class="risk">${escapeHtml((action.risk || "low").toUpperCase())}</span>
          </button>
        `)
        .join("");
    }

    function renderRunnerCommands(context) {
      const select = document.getElementById("command-select");
      select.innerHTML = context.runner_commands
        .map((command) => `<option value="${escapeHtml(command.name)}">${escapeHtml(command.name)}</option>`)
        .join("");
      if (!select.value && context.runner_commands.length > 0) {
        select.value = context.runner_commands[0].name;
      }
      renderGuide();
    }

    function renderGuide() {
      if (!appState.context) {
        return;
      }
      const commandName = document.getElementById("command-select").value;
      const guide = appState.context.guides[commandName];
      const metadata = appState.context.runner_commands.find((command) => command.name === commandName);
      document.getElementById("guide-risk").textContent = `${(guide?.risk || metadata?.risk || "low").toUpperCase()} risk`;

      if (!guide) {
        document.getElementById("guide-panel").innerHTML = `
          <div class="guide-block">
            <strong>${escapeHtml(metadata?.name || "command")}</strong>
            <div class="subtle" style="margin-top: 10px;">${escapeHtml(metadata?.description || "")}</div>
            <div class="note" style="margin-top: 12px;">Example: ${escapeHtml(metadata?.example || "")}</div>
          </div>
        `;
        return;
      }

      const flags = guide.flags.slice(0, 5).map((flag) => `<li><strong>${escapeHtml(flag.flag)}</strong> - ${escapeHtml(flag.description)}</li>`).join("");
      const examples = (guide.examples || []).map((example) => `<li>${escapeHtml(example)}</li>`).join("");
      const practices = guide.best_practices.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
      const warnings = guide.warnings.map((item) => `<li>${escapeHtml(item)}</li>`).join("");

      document.getElementById("guide-panel").innerHTML = `
        <div class="guide-block">
          <strong>${escapeHtml(commandName)}</strong>
          <div class="subtle" style="margin-top: 10px;">${escapeHtml(guide.description)}</div>
        </div>
        <div class="guide-block">
          <strong>Useful Flags</strong>
          <ul>${flags || "<li>No flag tips available.</li>"}</ul>
        </div>
        <div class="guide-block">
          <strong>Best Practices</strong>
          <ul>${practices || "<li>No best practices available.</li>"}</ul>
        </div>
        <div class="guide-block">
          <strong>Warnings</strong>
          <ul>${warnings || "<li>No warnings listed.</li>"}</ul>
        </div>
        <div class="guide-block">
          <strong>Examples</strong>
          <ul>${examples || "<li>No examples available.</li>"}</ul>
        </div>
      `;
    }

    function renderHistory(context) {
      const list = document.getElementById("history-list");
      if (!context.history.length) {
        list.innerHTML = `<div class="subtle">No history yet. Run a command from the browser or TUI.</div>`;
        return;
      }
      list.innerHTML = context.history
        .map((entry) => `
          <div class="list-item">
            <div>
              <strong>${escapeHtml(entry.command_name)}</strong>
              <small>${escapeHtml(entry.label)}</small>
            </div>
            <div class="mini-actions">
              <button class="secondary" data-load-command="${escapeHtml(entry.command_name)}" data-load-args="${escapeHtml(entry.raw_args || "")}">Load</button>
            </div>
          </div>
        `)
        .join("");
    }

    function renderFavorites(context) {
      const list = document.getElementById("favorites-list");
      if (!context.favorites.length) {
        list.innerHTML = `<div class="subtle">No favorites yet. Use Toggle Favorite to pin a workflow.</div>`;
        return;
      }
      list.innerHTML = context.favorites
        .map((entry) => `
          <div class="list-item">
            <div>
              <strong>${escapeHtml(entry.command_name)}</strong>
              <small>${escapeHtml(entry.label)}</small>
            </div>
            <div class="mini-actions">
              <button class="secondary" data-load-command="${escapeHtml(entry.command_name)}" data-load-args="${escapeHtml(entry.raw_args || "")}">Load</button>
              <button class="secondary" data-unfavorite-command="${escapeHtml(entry.command_name)}" data-unfavorite-args="${escapeHtml(entry.raw_args || "")}">Remove</button>
            </div>
          </div>
        `)
        .join("");
    }

    function renderState(context) {
      const state = context.state;
      const pills = [
        `Resources: ${state.resource_count}`,
        `Types: ${state.stats.resource_types || 0}`,
        `State: ${state.stats.has_state ? "present" : "not detected"}`
      ];
      if (state.stats.terraform_version) {
        pills.push(`Version: ${state.stats.terraform_version}`);
      }
      document.getElementById("state-pills").innerHTML = pills
        .map((item) => `<div class="pill">${escapeHtml(item)}</div>`)
        .join("");

      const list = document.getElementById("state-list");
      if (!state.resources.length) {
        list.innerHTML = `<div class="subtle">No state resources detected.</div>`;
        return;
      }

      list.innerHTML = state.resources
        .map((resource) => `
          <div class="list-item">
            <div>
              <strong>${escapeHtml(resource.address)}</strong>
              <small>${escapeHtml(resource.type)}</small>
            </div>
            <div class="mini-actions">
              <button class="secondary" data-state-address="${escapeHtml(resource.address)}">Inspect</button>
            </div>
          </div>
        `)
        .join("");
    }

    function renderWorkspaces(context) {
      const workspaceInfo = context.workspaces;
      const list = document.getElementById("workspace-list");
      if (!workspaceInfo.success) {
        list.innerHTML = `<div class="subtle">${escapeHtml(workspaceInfo.error || "Could not read workspaces.")}</div>`;
        return;
      }

      list.innerHTML = workspaceInfo.workspaces
        .map((workspace) => `
          <div class="list-item">
            <div>
              <strong>${escapeHtml(workspace)}</strong>
              <small>${workspace === workspaceInfo.current ? "Current workspace" : "Available workspace"}</small>
            </div>
            <div class="mini-actions">
              ${workspace === workspaceInfo.current ? '<span class="pill status-ready">CURRENT</span>' : ''}
            </div>
          </div>
        `)
        .join("");
    }

    function renderResult(result) {
      appState.lastResult = result;
      const body = document.getElementById("terminal-body");
      const command = document.getElementById("terminal-command");
      const meta = document.getElementById("terminal-meta");
      const status = document.getElementById("result-status");

      command.textContent = result.preview || "infra-guide";
      status.textContent = result.success ? "Completed" : "Needs attention";
      meta.textContent = `exit ${result.exit_code}`;

      if (result.kind === "runner") {
        const blocks = [];
        blocks.push(`
          <div class="terminal-block">
            <div class="pill-row">
              <div class="pill">${escapeHtml(result.summary)}</div>
              <div class="pill">Duration: ${escapeHtml(result.duration_seconds)}s</div>
            </div>
          </div>
        `);
        if (result.cost_preview) {
          const details = (result.cost_preview.details || []).map((line) => `<li>${escapeHtml(line)}</li>`).join("");
          blocks.push(`
            <div class="terminal-block">
              <strong>${escapeHtml(result.cost_preview.title)}</strong>
              <pre>${escapeHtml(result.cost_preview.summary)}</pre>
              <ul>${details}</ul>
            </div>
          `);
        }
        if (result.stdout) {
          blocks.push(`
            <div class="terminal-block">
              <strong>stdout</strong>
              <pre>${escapeHtml(result.stdout)}</pre>
            </div>
          `);
        }
        if (result.stderr) {
          blocks.push(`
            <div class="terminal-block">
              <strong>stderr</strong>
              <pre>${escapeHtml(result.stderr)}</pre>
            </div>
          `);
        }
        body.innerHTML = blocks.join("");
        return;
      }

      if (result.kind === "validation") {
        const checks = result.validation.checks.map((check) => `<li>${escapeHtml(check.name)}: ${escapeHtml(check.status)} - ${escapeHtml(check.message)}</li>`).join("");
        body.innerHTML = `
          <div class="terminal-block">
            <div class="pill-row">
              <div class="pill">Passed: ${escapeHtml(result.validation.passed)}</div>
              <div class="pill">Warnings: ${escapeHtml(result.validation.warnings)}</div>
              <div class="pill">Failed: ${escapeHtml(result.validation.failed)}</div>
            </div>
          </div>
          <div class="terminal-block">
            <strong>Validation checks</strong>
            <ul>${checks}</ul>
          </div>
        `;
        return;
      }

      if (result.kind === "doctor") {
        const validationChecks = result.validation.checks.map((check) => `<li>${escapeHtml(check.name)}: ${escapeHtml(check.status)} - ${escapeHtml(check.message)}</li>`).join("");
        const driftSection = result.drift ? `
          <div class="terminal-block">
            <strong>Drift</strong>
            <pre>${escapeHtml(JSON.stringify(result.drift, null, 2))}</pre>
          </div>
        ` : "";
        body.innerHTML = `
          <div class="terminal-block">
            <div class="pill-row">
              <div class="pill">Workspace: ${escapeHtml(result.snapshot.workspace)}</div>
              <div class="pill">Readiness: ${escapeHtml(result.snapshot.readiness_label)}</div>
              <div class="pill">Failed checks: ${escapeHtml(result.validation.failed)}</div>
            </div>
          </div>
          <div class="terminal-block">
            <strong>Recommendation</strong>
            <pre>${escapeHtml(result.snapshot.recommendation)}</pre>
          </div>
          <div class="terminal-block">
            <strong>Validation checks</strong>
            <ul>${validationChecks}</ul>
          </div>
          ${driftSection}
        `;
        return;
      }

      if (result.kind === "drift") {
        if (!result.drift.success) {
          body.innerHTML = `<div class="terminal-block"><pre>${escapeHtml(result.drift.error || "Drift detection failed.")}</pre></div>`;
          return;
        }
        const resources = (result.drift.drifted_resources || []).map((resource) => {
          const address = resource.resource ? resource.resource.addr : "unknown";
          return `<li>${escapeHtml(address)} - ${escapeHtml(resource.action || "unknown")}</li>`;
        }).join("");
        body.innerHTML = `
          <div class="terminal-block">
            <div class="pill-row">
              <div class="pill">Drift detected: ${result.drift.drift_detected ? "yes" : "no"}</div>
              <div class="pill">Count: ${escapeHtml(result.drift.drift_count || 0)}</div>
            </div>
          </div>
          <div class="terminal-block">
            <strong>Resources</strong>
            ${resources ? `<ul>${resources}</ul>` : `<pre>No drift detected.</pre>`}
          </div>
        `;
        return;
      }

      if (result.kind === "cicd") {
        const steps = result.pipeline.steps.map((step) => `
          <li>${escapeHtml(step.name)} - ${step.success ? "ok" : "failed"}</li>
        `).join("");
        body.innerHTML = `
          <div class="terminal-block">
            <div class="pill-row">
              <div class="pill">Pipeline: ${result.success ? "passed" : "failed"}</div>
              <div class="pill">Plan file: ${escapeHtml(result.pipeline.plan_file || "tfplan")}</div>
              <div class="pill">Has changes: ${result.pipeline.has_changes ? "yes" : "no"}</div>
            </div>
          </div>
          <div class="terminal-block">
            <strong>Steps</strong>
            <ul>${steps}</ul>
          </div>
          <div class="terminal-block">
            <strong>Raw details</strong>
            <pre>${escapeHtml(JSON.stringify(result.pipeline, null, 2))}</pre>
          </div>
        `;
        return;
      }

      body.innerHTML = `<div class="terminal-block"><pre>${escapeHtml(result.error || "Unknown error.")}</pre></div>`;
    }

    async function refreshContext() {
      const context = await api("/api/context");
      appState.context = context;
      renderHero(context);
      renderStats(context);
      renderThemeOptions(context);
      renderQuickActions(context);
      renderRunnerCommands(context);
      renderHistory(context);
      renderFavorites(context);
      renderState(context);
      renderWorkspaces(context);
    }

    function loadCommand(commandName, rawArgs) {
      document.getElementById("command-select").value = commandName;
      document.getElementById("args-input").value = rawArgs || "";
      renderGuide();
    }

    async function runRunnerCommand() {
      const commandName = document.getElementById("command-select").value;
      const rawArgs = document.getElementById("args-input").value;
      const confirmExecution = document.getElementById("confirm-select").value === "true";
      document.getElementById("result-status").textContent = "Running...";
      const result = await api("/api/run", {
        method: "POST",
        body: JSON.stringify({ command_name: commandName, raw_args: rawArgs, confirm_execution: confirmExecution })
      });
      renderResult(result);
      await refreshContext();
      loadCommand(commandName, rawArgs);
    }

    async function runQuickAction(commandName, rawArgs) {
      document.getElementById("result-status").textContent = "Running...";
      const result = await api("/api/run", {
        method: "POST",
        body: JSON.stringify({ command_name: commandName, raw_args: rawArgs, confirm_execution: true })
      });
      renderResult(result);
      await refreshContext();
    }

    async function toggleFavoriteCurrent() {
      const commandName = document.getElementById("command-select").value;
      const rawArgs = document.getElementById("args-input").value;
      await api("/api/favorite/toggle", {
        method: "POST",
        body: JSON.stringify({ command_name: commandName, raw_args: rawArgs })
      });
      await refreshContext();
      loadCommand(commandName, rawArgs);
    }

    async function showStateDetail(address) {
      const payload = await api(`/api/state/detail?address=${encodeURIComponent(address)}`);
      renderResult({
        kind: payload.success ? "state" : "error",
        success: payload.success,
        exit_code: payload.success ? 0 : 1,
        preview: `infra-guide state --detail ${address}`,
        error: payload.error,
        stdout: payload.detail,
        address: payload.address
      });

      if (payload.success) {
        document.getElementById("terminal-body").innerHTML = `
          <div class="terminal-block">
            <strong>State detail: ${escapeHtml(payload.address)}</strong>
            <pre>${escapeHtml(payload.detail)}</pre>
          </div>
        `;
      }
    }

    async function workspaceAction(action) {
      const name = document.getElementById("workspace-input").value.trim();
      const result = await api("/api/workspace", {
        method: "POST",
        body: JSON.stringify({ action, name })
      });
      await refreshContext();
      renderResult({
        kind: result.success ? "workspace" : "error",
        success: result.success,
        exit_code: result.success ? 0 : 1,
        preview: `infra-guide workspace ${action} ${name}`.trim(),
        error: result.error || result.stderr,
      });

      document.getElementById("terminal-body").innerHTML = `
        <div class="terminal-block">
          <strong>Workspace ${escapeHtml(action)}</strong>
          <pre>${escapeHtml(result.stdout || result.stderr || "Workspace action completed.")}</pre>
        </div>
      `;
    }

    function attachEvents() {
      document.getElementById("refresh-context").addEventListener("click", refreshContext);
      document.getElementById("clear-history").addEventListener("click", async () => {
        await api("/api/history/clear", { method: "POST", body: JSON.stringify({}) });
        await refreshContext();
      });
      document.getElementById("theme-select").addEventListener("change", async (event) => {
        await api("/api/theme", {
          method: "POST",
          body: JSON.stringify({ theme_name: event.target.value })
        });
        await refreshContext();
      });
      document.getElementById("command-select").addEventListener("change", renderGuide);
      document.getElementById("run-command").addEventListener("click", runRunnerCommand);
      document.getElementById("favorite-command").addEventListener("click", toggleFavoriteCurrent);
      document.getElementById("load-example").addEventListener("click", () => {
        const commandName = document.getElementById("command-select").value;
        const metadata = appState.context.runner_commands.find((command) => command.name === commandName);
        document.getElementById("args-input").value = metadata?.example || "";
      });
      document.getElementById("state-detail-button").addEventListener("click", () => {
        const address = document.getElementById("state-detail-input").value.trim();
        if (address) {
          showStateDetail(address);
        }
      });

      document.querySelectorAll("[data-workspace-action]").forEach((button) => {
        button.addEventListener("click", () => workspaceAction(button.dataset.workspaceAction));
      });

      document.body.addEventListener("click", async (event) => {
        const button = event.target.closest("button");
        if (!button) {
          return;
        }
        if (button.dataset.actionCommand) {
          await runQuickAction(button.dataset.actionCommand, button.dataset.actionArgs || "");
        }
        if (button.dataset.loadCommand) {
          loadCommand(button.dataset.loadCommand, button.dataset.loadArgs || "");
        }
        if (button.dataset.unfavoriteCommand) {
          await api("/api/favorite/toggle", {
            method: "POST",
            body: JSON.stringify({
              command_name: button.dataset.unfavoriteCommand,
              raw_args: button.dataset.unfavoriteArgs || ""
            })
          });
          await refreshContext();
        }
        if (button.dataset.stateAddress) {
          document.getElementById("state-detail-input").value = button.dataset.stateAddress;
          await showStateDetail(button.dataset.stateAddress);
        }
      });
    }

    window.addEventListener("DOMContentLoaded", async () => {
      attachEvents();
      await refreshContext();
      document.getElementById("terminal-body").innerHTML = `
        <div class="terminal-block">
          <pre>Ready. Choose a runner command or use a quick diagnostic action.</pre>
        </div>
      `;
    });
  </script>
</body>
</html>
"""
