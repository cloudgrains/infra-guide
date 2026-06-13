"""
Main CLI entry point for infra-guide.
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

from rich.prompt import Confirm, Prompt

from infra_guide import __version__
from infra_guide.cicd import CICDRunner
from infra_guide.cost_estimator import CostEstimator
from infra_guide.detector import ToolDetector
from infra_guide.drift_detector import DriftDetector
from infra_guide.guides import apply, destroy, init, plan
from infra_guide.policy_checker import PolicyChecker
from infra_guide.preferences import DEFAULT_THEME, THEMES, PreferencesStore
from infra_guide.project_inspector import ProjectInspector
from infra_guide.runner import CommandRunner
from infra_guide.state_explorer import StateExplorer
from infra_guide.ui import InfraGuideUI
from infra_guide.validators import PreFlightValidator
from infra_guide.web import WebCommandCenter
from infra_guide.workspace_manager import WorkspaceManager

GUIDE_MODULES = {
    "init": init,
    "plan": plan,
    "apply": apply,
    "destroy": destroy,
}

RISK_BY_COMMAND = {
    "doctor": "low",
    "history": "low",
    "theme": "low",
    "init": "low",
    "plan": "low",
    "apply": "medium",
    "destroy": "high",
    "validate": "low",
    "drift": "low",
    "state": "low",
    "workspace": "medium",
    "fmt": "low",
    "cicd": "medium",
    "output": "low",
    "policy": "low",
}


def build_parser() -> argparse.ArgumentParser:
    """Build the main argparse parser."""
    parser = argparse.ArgumentParser(
        prog="infra-guide",
        description="Product-grade CLI and command center for Terraform and OpenTofu.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  infra-guide\n"
            "  infra-guide doctor --with-drift\n"
            "  infra-guide theme --set sunset\n"
            "  infra-guide history --favorites\n"
            "  infra-guide web --port 9000\n"
            "  infra-guide plan --out tfplan\n"
            "  infra-guide apply --plan-file tfplan --yes\n"
            "  infra-guide plan -- --target=module.network"
        ),
    )
    parser.add_argument(
        "--tool",
        choices=["tofu", "terraform"],
        help="force a specific IaC tool instead of auto-detecting",
    )
    parser.add_argument(
        "--cwd",
        help="run infra-guide from a different working directory",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI styling in infra-guide output",
    )
    parser.add_argument(
        "--theme",
        choices=sorted(THEMES.keys()),
        help="preview a theme for this session without saving it",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("interactive", help="launch the interactive command center")
    subparsers.add_parser("status", help="show a fast workspace summary")

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="run workspace health checks with recommendations",
    )
    doctor_parser.add_argument(
        "--with-drift",
        action="store_true",
        help="also run a drift check after validation",
    )

    guide_parser = subparsers.add_parser(
        "guide",
        help="show guidance and best practices for a command",
    )
    guide_parser.add_argument("guide_command", choices=sorted(GUIDE_MODULES.keys()))

    history_parser = subparsers.add_parser(
        "history",
        help="show recent commands and favorites",
    )
    history_parser.add_argument(
        "--favorites",
        action="store_true",
        help="show favorites only",
    )
    history_parser.add_argument(
        "--clear",
        action="store_true",
        help="clear command history",
    )

    theme_parser = subparsers.add_parser(
        "theme",
        help="show or change the active TUI theme",
    )
    theme_parser.add_argument(
        "--list",
        action="store_true",
        help="list available themes",
    )
    theme_parser.add_argument(
        "--set",
        dest="set_theme_name",
        choices=sorted(THEMES.keys()),
        help="persist a theme for future runs",
    )

    web_parser = subparsers.add_parser(
        "web",
        help="launch the local browser command center",
    )
    web_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="bind the web UI to a host (default: 127.0.0.1)",
    )
    web_parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="bind the web UI to a port (default: 8765, use 0 for auto)",
    )
    web_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="start the server without opening a browser tab",
    )

    subparsers.add_parser("validate", help="run pre-flight validation checks")
    subparsers.add_parser("drift", help="detect infrastructure drift")

    state_parser = subparsers.add_parser("state", help="explore current state")
    state_parser.add_argument(
        "--list",
        dest="list_resources",
        action="store_true",
        help="list all resources in state",
    )
    state_parser.add_argument(
        "--tree",
        action="store_true",
        help="show a tree view of the state",
    )
    state_parser.add_argument(
        "--detail",
        metavar="ADDRESS",
        help="show detailed information for one resource",
    )

    workspace_parser = subparsers.add_parser("workspace", help="manage workspaces")
    workspace_parser.add_argument(
        "--list",
        dest="list_workspaces",
        action="store_true",
        help="list workspaces and show the current one",
    )
    workspace_parser.add_argument(
        "--select",
        dest="select_workspace",
        metavar="NAME",
        help="switch to an existing workspace",
    )
    workspace_parser.add_argument(
        "--create",
        dest="create_workspace",
        metavar="NAME",
        help="create a new workspace",
    )
    workspace_parser.add_argument(
        "--delete",
        dest="delete_workspace",
        metavar="NAME",
        help="delete a workspace",
    )

    fmt_parser = subparsers.add_parser("fmt", help="format Terraform/OpenTofu files")
    fmt_parser.add_argument(
        "--check",
        action="store_true",
        help="only check formatting without modifying files",
    )
    fmt_parser.add_argument(
        "--diff",
        action="store_true",
        help="show formatting differences",
    )
    fmt_parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="format only the current directory",
    )
    add_passthrough_args(fmt_parser)

    cicd_parser = subparsers.add_parser("cicd", help="run the CI/CD flow")
    cicd_parser.add_argument(
        "--skip-init",
        action="store_true",
        help="skip the init step",
    )
    cicd_parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="skip validation checks",
    )

    output_parser = subparsers.add_parser("output", help="show infrastructure output values")
    output_parser.add_argument(
        "output_name",
        nargs="?",
        default=None,
        metavar="NAME",
        help="show a single output value by name",
    )
    output_parser.add_argument(
        "--json", dest="output_json", action="store_true", help="emit raw JSON"
    )
    output_parser.add_argument(
        "--raw", dest="output_raw", action="store_true", help="print the value without formatting"
    )

    policy_parser = subparsers.add_parser(
        "policy", help="check plan against built-in security policies"
    )
    policy_parser.add_argument(
        "--plan-file",
        dest="policy_plan_file",
        metavar="PATH",
        help="saved plan file to analyse (JSON format required)",
    )

    init_parser = subparsers.add_parser("init", help="initialize a working directory")
    init_parser.add_argument("--upgrade", action="store_true", help="upgrade providers and modules")
    init_parser.add_argument(
        "--reconfigure", action="store_true", help="reconfigure backend settings"
    )
    init_parser.add_argument("--migrate-state", action="store_true", help="migrate backend state")
    init_parser.add_argument(
        "--backend-config",
        dest="backend_configs",
        action="append",
        default=[],
        metavar="PATH",
        help="backend config file or key=value pair",
    )
    init_parser.add_argument(
        "--no-get",
        action="store_true",
        help="skip module downloads",
    )
    add_passthrough_args(init_parser)

    plan_parser = subparsers.add_parser("plan", help="preview infrastructure changes")
    add_common_runtime_options(plan_parser, allow_target=True)
    plan_parser.add_argument("--out", metavar="PATH", help="save the plan to a file")
    plan_parser.add_argument(
        "--detailed-exitcode",
        action="store_true",
        help="return 2 when changes are present",
    )
    plan_parser.add_argument(
        "--destroy-mode",
        action="store_true",
        help="create a destroy plan instead of a change plan",
    )
    plan_parser.add_argument(
        "--refresh-only",
        action="store_true",
        help="check drift without proposing changes",
    )
    plan_parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="skip refreshing remote objects before planning",
    )
    plan_parser.add_argument(
        "--replace",
        dest="replacements",
        action="append",
        default=[],
        metavar="ADDRESS",
        help="force replacement for a resource address",
    )
    add_passthrough_args(plan_parser)

    apply_parser = subparsers.add_parser("apply", help="apply infrastructure changes")
    add_common_runtime_options(apply_parser, allow_target=True)
    apply_parser.add_argument(
        "--plan-file",
        metavar="PATH",
        help="apply a saved plan file",
    )
    apply_parser.add_argument(
        "--yes",
        action="store_true",
        help="skip infra-guide confirmation and pass -auto-approve",
    )
    apply_parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="skip refreshing remote objects before apply",
    )
    add_passthrough_args(apply_parser)

    destroy_parser = subparsers.add_parser("destroy", help="destroy managed infrastructure")
    add_common_runtime_options(destroy_parser, allow_target=True)
    destroy_parser.add_argument(
        "--yes",
        action="store_true",
        help="skip infra-guide confirmation and pass -auto-approve",
    )
    destroy_parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="skip refreshing remote objects before destroy",
    )
    add_passthrough_args(destroy_parser)

    return parser


def add_common_runtime_options(parser: argparse.ArgumentParser, allow_target: bool = True):
    """Add shared flags used by plan/apply/destroy commands."""
    parser.add_argument(
        "--var",
        dest="vars",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="set a root module variable",
    )
    parser.add_argument(
        "--var-file",
        dest="var_files",
        action="append",
        default=[],
        metavar="PATH",
        help="load variables from a file",
    )
    if allow_target:
        parser.add_argument(
            "--target",
            dest="targets",
            action="append",
            default=[],
            metavar="ADDRESS",
            help="limit the operation to a specific resource or module",
        )
    parser.add_argument(
        "--parallelism",
        type=int,
        metavar="N",
        help="limit concurrent operations",
    )
    parser.add_argument(
        "--lock-timeout",
        metavar="DURATION",
        help="retry duration for acquiring a state lock, for example 30s",
    )
    parser.add_argument(
        "--compact-warnings",
        action="store_true",
        help="request compact warning output from the IaC tool",
    )
    parser.add_argument(
        "--show-sensitive",
        action="store_true",
        help="show sensitive values when supported",
    )


def add_passthrough_args(parser: argparse.ArgumentParser):
    """Allow raw flags to be forwarded after '--'."""
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="raw flags to pass through after '--'",
    )


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the infra-guide CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cwd:
        try:
            os.chdir(args.cwd)
        except OSError as error:
            print(f"ERROR: could not change directory to '{args.cwd}': {error}", file=sys.stderr)
            return 2

    preferences = PreferencesStore()
    chosen_theme = (
        args.theme or getattr(args, "set_theme_name", None) or preferences.get_theme_name()
    )

    tool = args.tool or ToolDetector.detect()
    if tool is None:
        temp_ui = InfraGuideUI("none", "none", no_color=args.no_color, theme_name=chosen_theme)
        temp_ui.show_no_tool_error()
        return 1
    tool_version = ToolDetector.get_version(tool)

    ui = InfraGuideUI(tool, tool_version, no_color=args.no_color, theme_name=chosen_theme)

    services = {
        "runner": CommandRunner(tool),
        "drift_detector": DriftDetector(tool),
        "state_explorer": StateExplorer(tool),
        "workspace_manager": WorkspaceManager(tool),
        "validator": PreFlightValidator(tool),
        "cicd_runner": CICDRunner(tool),
        "inspector": ProjectInspector(tool),
        "preferences": preferences,
        "cost_estimator": CostEstimator(tool),
    }

    if args.command in (None, "interactive"):
        if args.command is None and not sys.stdin.isatty():
            parser.print_help()
            return 2
        ui.set_logo_visibility(True)
        return run_interactive_app(ui, services)

    return dispatch_command(args, ui, services)


def dispatch_command(args: argparse.Namespace, ui: InfraGuideUI, services: Dict[str, Any]) -> int:
    """Dispatch direct CLI commands."""
    if args.command == "status":
        snapshot = services["inspector"].inspect(include_state=False)
        ui.show_banner(snapshot=snapshot, title="Status")
        ui.show_project_status(snapshot)
        return 0

    if args.command == "doctor":
        return run_doctor(
            ui,
            services["inspector"],
            services["validator"],
            services["drift_detector"],
            with_drift=args.with_drift,
        )

    if args.command == "guide":
        return show_guide_command(ui, services["inspector"], args.guide_command)

    if args.command == "history":
        return run_history_command(args, ui, services["preferences"])

    if args.command == "theme":
        return run_theme_command(args, ui, services["preferences"])

    if args.command == "web":
        return run_web_command(
            args,
            services,
            tool_name=ui.tool_name,
            tool_version=ui.tool_version,
            theme_name=ui.theme_name,
        )

    if args.command == "validate":
        results = services["validator"].run_all_checks()
        services["validator"].show_validation_report(results)
        return 1 if results["failed"] > 0 else 0

    if args.command == "drift":
        drift_data = services["drift_detector"].detect_drift()
        services["drift_detector"].show_drift_report(drift_data)
        if not drift_data.get("success"):
            return 1
        return 2 if drift_data.get("drift_detected") else 0

    if args.command == "state":
        return run_state_command(args, services["state_explorer"])

    if args.command == "workspace":
        return run_workspace_command(args, services["workspace_manager"])

    if args.command == "fmt":
        command_args = build_fmt_args(args)
        return execute_direct_command(
            command_name="fmt",
            command_args=command_args,
            ui=ui,
            runner=services["runner"],
            inspector=services["inspector"],
            preferences=services["preferences"],
            cost_estimator=services["cost_estimator"],
        )

    if args.command == "cicd":
        success = services["cicd_runner"].run_full_pipeline(
            skip_init=args.skip_init,
            skip_validation=args.skip_validation,
        )
        return 0 if success else 1

    if args.command == "output":
        return run_output_command(args, ui, services["runner"])

    if args.command == "policy":
        return run_policy_command(args, ui, services["runner"])

    if args.command in GUIDE_MODULES:
        command_args = build_command_args(args.command, args)
        return execute_direct_command(
            command_name=args.command,
            command_args=command_args,
            ui=ui,
            runner=services["runner"],
            inspector=services["inspector"],
            preferences=services["preferences"],
            cost_estimator=services["cost_estimator"],
            require_confirmation=args.command in ("apply", "destroy"),
            auto_confirm=getattr(args, "yes", False),
            detailed_exitcode=getattr(args, "detailed_exitcode", False),
        )

    ui.show_error(f"Unknown command: {args.command}")
    return 2


def run_interactive_app(ui: InfraGuideUI, services: Dict[str, Any]) -> int:
    """Run the interactive command center."""
    while True:
        snapshot = services["inspector"].inspect(include_state=False)
        ui.clear_screen()
        ui.show_dashboard(
            snapshot,
            history_entries=services["preferences"].get_history(limit=6),
            favorites=services["preferences"].get_favorites(),
        )

        choice = ui.show_menu()

        if choice == "1":
            ui.clear_screen()
            run_doctor(
                ui,
                services["inspector"],
                services["validator"],
                services["drift_detector"],
                with_drift=False,
                title="Doctor",
            )
            ui.wait_for_enter()
        elif choice == "2":
            run_guided_command(
                "init",
                ui,
                services["runner"],
                services["inspector"],
                services["preferences"],
                services["cost_estimator"],
            )
        elif choice == "3":
            run_guided_command(
                "plan",
                ui,
                services["runner"],
                services["inspector"],
                services["preferences"],
                services["cost_estimator"],
            )
        elif choice == "4":
            run_guided_command(
                "apply",
                ui,
                services["runner"],
                services["inspector"],
                services["preferences"],
                services["cost_estimator"],
            )
        elif choice == "5":
            run_guided_command(
                "destroy",
                ui,
                services["runner"],
                services["inspector"],
                services["preferences"],
                services["cost_estimator"],
            )
        elif choice == "6":
            ui.clear_screen()
            ui.show_banner(snapshot=services["inspector"].inspect(), title="Validate")
            results = services["validator"].run_all_checks()
            services["validator"].show_validation_report(results)
            ui.wait_for_enter()
        elif choice == "7":
            ui.clear_screen()
            ui.show_banner(snapshot=services["inspector"].inspect(), title="Drift Detection")
            ui.show_info("Detecting infrastructure drift...")
            drift_data = services["drift_detector"].detect_drift()
            services["drift_detector"].show_drift_report(drift_data)
            ui.wait_for_enter()
        elif choice == "8":
            handle_state_menu(ui, services["state_explorer"], services["inspector"])
        elif choice == "9":
            services["workspace_manager"].show_workspace_menu()
        elif choice == "10":
            handle_history_menu(
                ui,
                services["preferences"],
                services["runner"],
                services["inspector"],
                services["cost_estimator"],
            )
        elif choice == "11":
            handle_theme_menu(ui, services["preferences"], services["inspector"])
        elif choice == "12":
            handle_fmt_menu(
                ui,
                services["runner"],
                services["inspector"],
                services["preferences"],
                services["cost_estimator"],
            )
        elif choice == "13":
            handle_cicd_menu(ui, services["cicd_runner"], services["inspector"])
        elif choice == "14":
            ui.clear_screen()
            ui.show_banner(
                snapshot=services["inspector"].inspect(include_state=False),
                title="Web Command Center",
            )
            ui.show_info(
                "Launching the local web UI on an available localhost port. Press Ctrl+C there to return."
            )
            run_web_launcher(
                tool_name=ui.tool_name,
                tool_version=ui.tool_version,
                services=services,
                theme_name=ui.theme_name,
                host="127.0.0.1",
                port=0,
                open_browser=True,
            )
        elif choice == "15":
            handle_output_menu(ui, services["runner"], services["inspector"])
        elif choice == "16":
            handle_policy_menu(ui, services["runner"], services["inspector"])
        elif choice == "0":
            ui.clear_screen()
            ui.show_goodbye()
            return 0


def show_guide_command(ui: InfraGuideUI, inspector: ProjectInspector, command_name: str) -> int:
    """Display a guide for a direct CLI command."""
    snapshot = inspector.inspect(include_state=False)
    guide_data = GUIDE_MODULES[command_name].get_guide()
    ui.show_banner(snapshot=snapshot, title=f"{command_name} Guide")
    ui.show_guide(
        title=command_name,
        description=guide_data["description"],
        flags=guide_data["flags"],
        best_practices=guide_data["best_practices"],
        warnings=guide_data["warnings"],
        risk_level=guide_data.get("risk", RISK_BY_COMMAND.get(command_name, "low")),
        examples=guide_data.get("examples"),
    )
    return 0


def run_guided_command(
    command_name: str,
    ui: InfraGuideUI,
    runner: CommandRunner,
    inspector: ProjectInspector,
    preferences: PreferencesStore,
    cost_estimator: CostEstimator,
):
    """Run an interactive guide-first command flow."""
    guide_data = GUIDE_MODULES[command_name].get_guide()
    snapshot = inspector.inspect(include_state=False)

    ui.clear_screen()
    ui.show_banner(snapshot=snapshot, title=f"{command_name} Guide")
    ui.show_guide(
        title=command_name,
        description=guide_data["description"],
        flags=guide_data["flags"],
        best_practices=guide_data["best_practices"],
        warnings=guide_data["warnings"],
        risk_level=guide_data.get("risk", RISK_BY_COMMAND.get(command_name, "low")),
        examples=guide_data.get("examples"),
    )

    extra_args = ui.prompt_for_extra_args()
    preview = runner.format_command(command_name, extra_args)
    is_favorite = preferences.is_favorite(command_name, extra_args)
    ui.show_command_preview(
        preview,
        risk_level=guide_data.get("risk", RISK_BY_COMMAND.get(command_name, "low")),
        is_favorite=is_favorite,
    )

    if ui.prompt_favorite_action(is_favorite):
        enabled = preferences.toggle_favorite(command_name, extra_args, preview)
        if enabled:
            ui.show_success("Command added to favorites.")
        else:
            ui.show_info("Command removed from favorites.")

    if command_name == "apply":
        ui.show_cost_preview(cost_estimator.estimate_apply_cost(extra_args))

    if ui.confirm_execution(
        preview,
        risk_level=guide_data.get("risk", RISK_BY_COMMAND.get(command_name, "low")),
    ):
        ui.show_command_output_header(preview)
        return_code = runner.execute(command_name, extra_args)
        preferences.record_execution(command_name, extra_args, preview, os.getcwd(), return_code)
        summarize_command_result(
            ui,
            command_name,
            return_code,
            detailed_exitcode=_uses_detailed_exitcode(command_name, extra_args),
        )
    else:
        ui.show_info("Command cancelled.")

    ui.wait_for_enter()


def execute_direct_command(
    command_name: str,
    command_args: List[str],
    ui: InfraGuideUI,
    runner: CommandRunner,
    inspector: ProjectInspector,
    preferences: PreferencesStore,
    cost_estimator: CostEstimator,
    require_confirmation: bool = False,
    auto_confirm: bool = False,
    detailed_exitcode: bool = False,
) -> int:
    """Execute a direct command with a product-style summary and exit code handling."""
    snapshot = inspector.inspect(include_state=False)
    ui.show_banner(snapshot=snapshot, title=command_name)
    ui.show_project_status(snapshot, title="Workspace Snapshot")

    preview = runner.format_command(command_name, command_args)
    risk_level = RISK_BY_COMMAND.get(command_name, "low")
    ui.show_command_preview(
        preview,
        risk_level=risk_level,
        is_favorite=preferences.is_favorite(command_name, command_args),
    )

    if command_name == "apply":
        ui.show_cost_preview(cost_estimator.estimate_apply_cost(command_args))

    if require_confirmation:
        if not auto_confirm and not sys.stdin.isatty():
            ui.show_error(
                f"Non-interactive '{command_name}' requires --yes so the underlying tool can run without prompts."
            )
            return 2

        if (
            not auto_confirm
            and sys.stdin.isatty()
            and not ui.confirm_execution(preview, risk_level=risk_level)
        ):
            ui.show_info("Command cancelled.")
            return 130

    ui.show_command_output_header(preview)
    return_code = runner.execute(command_name, command_args)
    preferences.record_execution(command_name, command_args, preview, os.getcwd(), return_code)
    summarize_command_result(ui, command_name, return_code, detailed_exitcode=detailed_exitcode)
    return return_code


def summarize_command_result(
    ui: InfraGuideUI, command_name: str, return_code: int, detailed_exitcode: bool = False
):
    """Display a friendly summary after command execution."""
    if detailed_exitcode and command_name == "plan" and return_code == 2:
        ui.show_info("Plan completed successfully and detected infrastructure changes.")
        return

    if return_code == 0:
        ui.show_success(f"{command_name} completed successfully.")
    else:
        ui.show_error(f"{command_name} exited with code {return_code}.")


def run_doctor(
    ui: InfraGuideUI,
    inspector: ProjectInspector,
    validator: PreFlightValidator,
    drift_detector: DriftDetector,
    with_drift: bool = False,
    title: str = "Doctor",
) -> int:
    """Run the doctor flow."""
    snapshot = inspector.inspect(include_state=True)
    ui.show_banner(snapshot=snapshot, title=title)
    ui.show_project_status(snapshot, title="Doctor Overview")

    ui.show_info("Running pre-flight checks...")
    validation_results = validator.run_all_checks()
    validator.show_validation_report(validation_results)

    if with_drift:
        ui.show_info("Running drift detection...")
        drift_data = drift_detector.detect_drift()
        drift_detector.show_drift_report(drift_data)
        if not drift_data.get("success"):
            return 1

    return 1 if validation_results["failed"] > 0 else 0


def run_state_command(args: argparse.Namespace, state_explorer: StateExplorer) -> int:
    """Run one of the state explorer direct commands."""
    if args.detail:
        state_explorer.show_resource_detail_panel(args.detail)
        return 0

    if args.list_resources:
        state_explorer.show_resources_list()
        return 0

    if args.tree:
        state_explorer.show_resource_tree()
        return 0

    state_explorer.show_state_overview()
    return 0


def run_workspace_command(args: argparse.Namespace, workspace_manager: WorkspaceManager) -> int:
    """Run direct workspace commands."""
    if args.create_workspace:
        result = workspace_manager.create_workspace(args.create_workspace)
        if result["success"]:
            workspace_manager.console.print(
                f"[bold green]OK[/bold green] Created workspace: {args.create_workspace}"
            )
            return 0

        workspace_manager.console.print(
            f"[bold red]ERROR[/bold red] {result['stderr'] or 'Failed to create workspace.'}"
        )
        return 1

    if args.select_workspace:
        result = workspace_manager.select_workspace(args.select_workspace)
        if result["success"]:
            workspace_manager.console.print(
                f"[bold green]OK[/bold green] Switched to workspace: {args.select_workspace}"
            )
            return 0

        workspace_manager.console.print(
            f"[bold red]ERROR[/bold red] {result['stderr'] or 'Failed to switch workspace.'}"
        )
        return 1

    if args.delete_workspace:
        result = workspace_manager.delete_workspace(args.delete_workspace)
        if result["success"]:
            workspace_manager.console.print(
                f"[bold green]OK[/bold green] Deleted workspace: {args.delete_workspace}"
            )
            return 0

        workspace_manager.console.print(
            f"[bold red]ERROR[/bold red] {result['stderr'] or 'Failed to delete workspace.'}"
        )
        return 1

    if args.list_workspaces or not sys.stdin.isatty():
        ws_info = workspace_manager.show_workspace_overview()
        return 0 if ws_info.get("success") else 1

    workspace_manager.show_workspace_menu()
    return 0


def run_history_command(
    args: argparse.Namespace, ui: InfraGuideUI, preferences: PreferencesStore
) -> int:
    """Run direct history commands."""
    if args.clear:
        preferences.clear_history()
        ui.show_success("Command history cleared.")
        return 0

    ui.show_banner(title="History")
    if args.favorites:
        ui.show_history_center([], preferences.get_favorites())
    else:
        ui.show_history_center(preferences.get_history(limit=12), preferences.get_favorites())
    return 0


def run_theme_command(
    args: argparse.Namespace, ui: InfraGuideUI, preferences: PreferencesStore
) -> int:
    """Run direct theme commands."""
    if args.set_theme_name:
        preferences.set_theme(args.set_theme_name)
        ui.set_theme(args.set_theme_name)
        ui.show_success(f"Theme set to {args.set_theme_name}.")

    ui.show_banner(title="Themes")
    ui.show_theme_gallery(preferences.get_theme_name())
    if not args.list and not args.set_theme_name:
        ui.show_info(f"Current theme: {preferences.get_theme_name()}")
    return 0


def run_web_command(
    args: argparse.Namespace,
    services: Dict[str, Any],
    tool_name: str,
    tool_version: str,
    theme_name: str,
) -> int:
    """Launch the local web command center."""
    return run_web_launcher(
        tool_name=tool_name,
        tool_version=tool_version,
        services=services,
        theme_name=theme_name,
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
    )


def run_web_launcher(
    tool_name: str,
    tool_version: str,
    services: Dict[str, Any],
    theme_name: str,
    host: str,
    port: int,
    open_browser: bool,
) -> int:
    """Start the web UI server."""
    web_app = WebCommandCenter(
        tool_name=tool_name,
        tool_version=tool_version,
        services=services,
        host=host,
        port=port,
        open_browser=open_browser,
        theme_name=theme_name,
    )
    return web_app.serve()


def handle_state_menu(ui: InfraGuideUI, state_explorer: StateExplorer, inspector: ProjectInspector):
    """Interactive state explorer menu."""
    while True:
        ui.clear_screen()
        ui.show_banner(snapshot=inspector.inspect(include_state=True), title="State Explorer")

        ui.console.print("\n[bold cyan]State Explorer[/bold cyan]\n")
        ui.console.print("1. Overview")
        ui.console.print("2. List resources")
        ui.console.print("3. Resource tree")
        ui.console.print("4. Resource detail")
        ui.console.print("5. Back to main menu\n")

        choice = Prompt.ask(
            "[cyan]Select option[/cyan]",
            choices=["1", "2", "3", "4", "5"],
            default="5",
        )

        if choice == "1":
            state_explorer.show_state_overview()
            ui.wait_for_enter()
        elif choice == "2":
            state_explorer.show_resources_list()
            ui.wait_for_enter()
        elif choice == "3":
            state_explorer.show_resource_tree()
            ui.wait_for_enter()
        elif choice == "4":
            resource_address = Prompt.ask("[cyan]Enter resource address[/cyan]").strip()
            if resource_address:
                state_explorer.show_resource_detail_panel(resource_address)
            ui.wait_for_enter()
        elif choice == "5":
            break


def handle_fmt_menu(
    ui: InfraGuideUI,
    runner: CommandRunner,
    inspector: ProjectInspector,
    preferences: PreferencesStore,
    cost_estimator: CostEstimator,
):
    """Interactive formatter flow."""
    ui.clear_screen()
    snapshot = inspector.inspect(include_state=False)
    ui.show_banner(snapshot=snapshot, title="Formatter")
    ui.show_project_status(snapshot, title="Workspace Snapshot")
    ui.show_info("This will run a recursive format across the current workspace.")

    extra_args = ui.prompt_for_extra_args()
    command_args = ["-recursive"] + extra_args
    preview = runner.format_command("fmt", command_args)
    ui.show_command_preview(
        preview,
        risk_level="low",
        is_favorite=preferences.is_favorite("fmt", command_args),
    )

    if ui.confirm_execution(preview, risk_level="low"):
        ui.show_command_output_header(preview)
        return_code = runner.execute("fmt", command_args)
        preferences.record_execution("fmt", command_args, preview, os.getcwd(), return_code)
        summarize_command_result(ui, "fmt", return_code)
    else:
        ui.show_info("Formatting cancelled.")

    ui.wait_for_enter()


def handle_cicd_menu(ui: InfraGuideUI, cicd_runner: CICDRunner, inspector: ProjectInspector):
    """Interactive CI/CD flow."""
    ui.clear_screen()
    ui.show_banner(snapshot=inspector.inspect(include_state=False), title="CI/CD")
    ui.show_info(
        "This runs init, validation, and plan in a non-interactive pipeline-friendly flow."
    )

    if Confirm.ask("[cyan]Run the CI/CD pipeline now?[/cyan]", default=False):
        success = cicd_runner.run_full_pipeline()
        if success:
            ui.show_success("CI/CD pipeline completed successfully.")
        else:
            ui.show_error("CI/CD pipeline failed. Review the output above.")
    else:
        ui.show_info("Pipeline cancelled.")

    ui.wait_for_enter()


def handle_history_menu(
    ui: InfraGuideUI,
    preferences: PreferencesStore,
    runner: CommandRunner,
    inspector: ProjectInspector,
    cost_estimator: CostEstimator,
):
    """Interactive history and favorites center."""
    while True:
        ui.clear_screen()
        ui.show_banner(snapshot=inspector.inspect(include_state=False), title="History & Favorites")
        ui.show_history_center(preferences.get_history(limit=10), preferences.get_favorites())

        ui.console.print("1. Rerun recent command")
        ui.console.print("2. Toggle favorite from recent command")
        ui.console.print("3. Run favorite")
        ui.console.print("4. Remove favorite")
        ui.console.print("5. Clear history")
        ui.console.print("6. Back to main menu\n")

        choice = Prompt.ask(
            "[cyan]Select option[/cyan]",
            choices=["1", "2", "3", "4", "5", "6"],
            default="6",
        )

        if choice == "1":
            history_entries = preferences.get_history(limit=10)
            entry = _select_saved_entry(history_entries, "recent command")
            if entry:
                execute_direct_command(
                    command_name=entry["command_name"],
                    command_args=list(entry.get("args", [])),
                    ui=ui,
                    runner=runner,
                    inspector=inspector,
                    preferences=preferences,
                    cost_estimator=cost_estimator,
                    require_confirmation=entry["command_name"] in ("apply", "destroy"),
                    detailed_exitcode=_uses_detailed_exitcode(
                        entry["command_name"], list(entry.get("args", []))
                    ),
                )
                ui.wait_for_enter()
        elif choice == "2":
            history_entries = preferences.get_history(limit=10)
            entry = _select_saved_entry(history_entries, "recent command")
            if entry:
                enabled = preferences.toggle_favorite(
                    entry["command_name"],
                    list(entry.get("args", [])),
                    entry.get("label", entry["command_name"]),
                )
                if enabled:
                    ui.show_success("Command added to favorites.")
                else:
                    ui.show_info("Command removed from favorites.")
                ui.wait_for_enter()
        elif choice == "3":
            favorites = preferences.get_favorites()
            entry = _select_saved_entry(favorites, "favorite")
            if entry:
                execute_direct_command(
                    command_name=entry["command_name"],
                    command_args=list(entry.get("args", [])),
                    ui=ui,
                    runner=runner,
                    inspector=inspector,
                    preferences=preferences,
                    cost_estimator=cost_estimator,
                    require_confirmation=entry["command_name"] in ("apply", "destroy"),
                    detailed_exitcode=_uses_detailed_exitcode(
                        entry["command_name"], list(entry.get("args", []))
                    ),
                )
                ui.wait_for_enter()
        elif choice == "4":
            favorites = preferences.get_favorites()
            entry = _select_saved_entry(favorites, "favorite")
            if entry:
                if preferences.remove_favorite(entry["key"]):
                    ui.show_success("Favorite removed.")
                else:
                    ui.show_error("Could not remove favorite.")
                ui.wait_for_enter()
        elif choice == "5":
            if Confirm.ask("[yellow]Clear command history?[/yellow]", default=False):
                preferences.clear_history()
                ui.show_success("Command history cleared.")
            else:
                ui.show_info("History clear cancelled.")
            ui.wait_for_enter()
        elif choice == "6":
            break


def handle_theme_menu(
    ui: InfraGuideUI,
    preferences: PreferencesStore,
    inspector: ProjectInspector,
):
    """Interactive theme customization center."""
    while True:
        ui.clear_screen()
        ui.show_banner(snapshot=inspector.inspect(include_state=False), title="Theme Studio")
        ui.show_theme_gallery(preferences.get_theme_name())

        theme_choices = list(sorted(THEMES.keys())) + ["back"]
        ui.console.print(f"Active theme: [bold]{preferences.get_theme_name()}[/bold]\n")
        selected = Prompt.ask(
            "[cyan]Choose a theme or back[/cyan]",
            choices=theme_choices,
            default="back",
        )

        if selected == "back":
            break

        preferences.set_theme(selected)
        ui.set_theme(selected)
        ui.show_success(f"Theme changed to {selected}.")
        ui.wait_for_enter()


def run_output_command(args: argparse.Namespace, ui: InfraGuideUI, runner: CommandRunner) -> int:
    """Show terraform/tofu output values."""
    cmd_args: List[str] = []
    if getattr(args, "output_json", False):
        cmd_args.append("-json")
    if getattr(args, "output_raw", False):
        cmd_args.append("-raw")
    if getattr(args, "output_name", None):
        cmd_args.append(args.output_name)

    result = runner.execute_capture("output", cmd_args)
    ui.show_output_panel(result.get("stdout", ""), runner.format_command("output", cmd_args))
    if result.get("stderr"):
        ui.show_error(result["stderr"].strip())
    return 0 if result["success"] else result["exit_code"]


def run_policy_command(args: argparse.Namespace, ui: InfraGuideUI, runner: CommandRunner) -> int:
    """Run policy checks against a plan file."""
    plan_file = getattr(args, "policy_plan_file", None)
    return _do_policy_check(ui, runner, plan_file)


def handle_output_menu(ui: InfraGuideUI, runner: CommandRunner, inspector: ProjectInspector):
    """Interactive output viewer."""
    ui.clear_screen()
    ui.show_banner(snapshot=inspector.inspect(include_state=False), title="Output Values")
    ui.show_info("Fetching all declared outputs from the current workspace...")
    result = runner.execute_capture("output", [])
    ui.show_output_panel(result.get("stdout", ""), runner.format_command("output", []))
    if result.get("stderr"):
        ui.show_error(result["stderr"].strip())
    ui.wait_for_enter()


def handle_policy_menu(ui: InfraGuideUI, runner: CommandRunner, inspector: ProjectInspector):
    """Interactive policy checker flow."""
    ui.clear_screen()
    ui.show_banner(snapshot=inspector.inspect(include_state=False), title="Policy Checker")
    ui.show_info(
        "Policy checks validate your plan against built-in security and compliance rules.\n"
        "  Provide a saved plan file path, or press Enter to skip."
    )
    plan_file = Prompt.ask("[cyan]Plan file path (optional)[/cyan]", default="").strip() or None
    _do_policy_check(ui, runner, plan_file)
    ui.wait_for_enter()


def _do_policy_check(ui: InfraGuideUI, runner: CommandRunner, plan_file: Optional[str]) -> int:
    """Run policy checks and display results. Returns exit code."""
    checker = PolicyChecker()
    if plan_file:
        result = runner.execute_capture("show", ["-json", plan_file])
        if not result["success"]:
            ui.show_error(f"Could not read plan file '{plan_file}': {result.get('stderr', '')}")
            return 1
        plan_json = result["stdout"]
    else:
        result = runner.execute_capture("show", ["-json"])
        if not result["success"] or not result["stdout"].strip():
            ui.show_info(
                "No plan file given and no current state to inspect. "
                "Run `infra-guide plan --out tfplan` then `infra-guide policy --plan-file tfplan`."
            )
            return 0
        plan_json = result["stdout"]

    results = checker.check_plan(plan_json)
    ui.show_policy_panel(results)
    return 1 if results.get("violations", 0) > 0 else 0


def build_command_args(command_name: str, args: argparse.Namespace) -> List[str]:
    """Build command arguments for init/plan/apply/destroy."""
    if command_name == "init":
        command_args = []
        if args.no_color:
            command_args.append("-no-color")
        if args.upgrade:
            command_args.append("-upgrade")
        if args.reconfigure:
            command_args.append("-reconfigure")
        if args.migrate_state:
            command_args.append("-migrate-state")
        for backend_config in args.backend_configs:
            command_args.append(f"-backend-config={backend_config}")
        if args.no_get:
            command_args.append("-get=false")
        command_args.extend(clean_passthrough_args(args.extra_args))
        return command_args

    if command_name == "plan":
        command_args = build_common_command_args(args)
        if args.out:
            command_args.append(f"-out={args.out}")
        if args.detailed_exitcode:
            command_args.append("-detailed-exitcode")
        if args.destroy_mode:
            command_args.append("-destroy")
        if args.refresh_only:
            command_args.append("-refresh-only")
        if args.no_refresh:
            command_args.append("-refresh=false")
        for replacement in args.replacements:
            command_args.extend(["-replace", replacement])
        command_args.extend(clean_passthrough_args(args.extra_args))
        return command_args

    if command_name == "apply":
        command_args = build_common_command_args(args)
        if args.yes:
            command_args.append("-auto-approve")
        if args.no_refresh:
            command_args.append("-refresh=false")
        if args.plan_file:
            command_args.append(args.plan_file)
        command_args.extend(clean_passthrough_args(args.extra_args))
        return command_args

    if command_name == "destroy":
        command_args = build_common_command_args(args)
        if args.yes:
            command_args.append("-auto-approve")
        if args.no_refresh:
            command_args.append("-refresh=false")
        command_args.extend(clean_passthrough_args(args.extra_args))
        return command_args

    return clean_passthrough_args(getattr(args, "extra_args", []))


def build_common_command_args(args: argparse.Namespace) -> List[str]:
    """Build shared plan/apply/destroy arguments."""
    command_args = []

    if getattr(args, "no_color", False):
        command_args.append("-no-color")
    if getattr(args, "compact_warnings", False):
        command_args.append("-compact-warnings")
    if getattr(args, "show_sensitive", False):
        command_args.append("-show-sensitive")
    if getattr(args, "parallelism", None) is not None:
        command_args.append(f"-parallelism={args.parallelism}")
    if getattr(args, "lock_timeout", None):
        command_args.append(f"-lock-timeout={args.lock_timeout}")

    for variable in getattr(args, "vars", []):
        command_args.extend(["-var", variable])

    for var_file in getattr(args, "var_files", []):
        command_args.extend(["-var-file", var_file])

    for target in getattr(args, "targets", []):
        command_args.extend(["-target", target])

    return command_args


def build_fmt_args(args: argparse.Namespace) -> List[str]:
    """Build arguments for the fmt command."""
    command_args = []
    if args.no_color:
        command_args.append("-no-color")
    if args.check:
        command_args.append("-check")
    if args.diff:
        command_args.append("-diff")
    if not args.no_recursive:
        command_args.append("-recursive")
    command_args.extend(clean_passthrough_args(args.extra_args))
    return command_args


def clean_passthrough_args(extra_args: List[str]) -> List[str]:
    """Normalize argparse remainder arguments."""
    passthrough = list(extra_args or [])
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    return passthrough


def _select_saved_entry(entries: List[Dict[str, Any]], label: str) -> Optional[Dict[str, Any]]:
    if not entries:
        return None

    for index, entry in enumerate(entries, 1):
        print(f"{index}. {entry.get('label', entry.get('command_name', 'command'))}")

    raw_value = Prompt.ask(f"[cyan]Select {label} number[/cyan]", default="")
    if not raw_value.isdigit():
        return None

    selected_index = int(raw_value)
    if selected_index < 1 or selected_index > len(entries):
        return None

    return entries[selected_index - 1]


def _uses_detailed_exitcode(command_name: str, args: List[str]) -> bool:
    return command_name == "plan" and "-detailed-exitcode" in args


if __name__ == "__main__":
    sys.exit(main())
