"""
Project inspection utilities for dashboards and readiness checks.
"""

from dataclasses import asdict, dataclass
import os
import re
import subprocess
from typing import Any, Dict, Optional, Tuple


MODULE_BLOCK_PATTERN = re.compile(r'\bmodule\s+"[^"]+"')
BACKEND_BLOCK_PATTERN = re.compile(r'\bbackend\s+"[^"]+"')


@dataclass
class ProjectSnapshot:
    """Structured view of the current infrastructure workspace."""

    cwd: str
    tool_name: str
    workspace: str
    tf_file_count: int
    tfvars_file_count: int
    module_block_count: int
    initialized: bool
    lock_file_present: bool
    backend_configured: bool
    state_present: Optional[bool]
    state_resource_count: Optional[int]
    readiness: str
    readiness_label: str
    recommendation: str

    def as_dict(self) -> Dict[str, Any]:
        """Return the snapshot as a plain dictionary."""
        return asdict(self)


class ProjectInspector:
    """Collects project metadata to power product-like CLI views."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name

    def inspect(self, include_state: bool = False) -> Dict[str, Any]:
        """Inspect the current directory and return a normalized snapshot."""
        tf_files = sorted(
            filename for filename in os.listdir(".") if filename.endswith(".tf")
        )
        tfvars_files = sorted(
            filename
            for filename in os.listdir(".")
            if filename.endswith(".tfvars") or filename.endswith(".auto.tfvars")
        )

        module_block_count = self._count_pattern_matches(tf_files, MODULE_BLOCK_PATTERN)
        backend_configured = (
            self._count_pattern_matches(tf_files, BACKEND_BLOCK_PATTERN) > 0
        )
        initialized = os.path.isdir(".terraform")
        lock_file_present = os.path.exists(".terraform.lock.hcl")
        workspace = self._get_current_workspace()

        if include_state:
            state_present, state_resource_count = self._get_state_summary()
        else:
            state_present, state_resource_count = self._guess_state_summary()

        readiness, readiness_label, recommendation = self._evaluate_readiness(
            tf_file_count=len(tf_files),
            initialized=initialized,
            backend_configured=backend_configured,
            lock_file_present=lock_file_present,
            state_present=state_present,
        )

        return ProjectSnapshot(
            cwd=os.getcwd(),
            tool_name=self.tool_name,
            workspace=workspace,
            tf_file_count=len(tf_files),
            tfvars_file_count=len(tfvars_files),
            module_block_count=module_block_count,
            initialized=initialized,
            lock_file_present=lock_file_present,
            backend_configured=backend_configured,
            state_present=state_present,
            state_resource_count=state_resource_count,
            readiness=readiness,
            readiness_label=readiness_label,
            recommendation=recommendation,
        ).as_dict()

    def _count_pattern_matches(self, tf_files, pattern: re.Pattern) -> int:
        count = 0
        for filename in tf_files:
            try:
                with open(filename, "r", encoding="utf-8", errors="ignore") as handle:
                    count += len(pattern.findall(handle.read()))
            except OSError:
                continue
        return count

    def _get_current_workspace(self) -> str:
        try:
            result = subprocess.run(
                [self.tool_name, "workspace", "show"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

        return "unknown"

    def _guess_state_summary(self) -> Tuple[Optional[bool], Optional[int]]:
        state_files = [
            "terraform.tfstate",
            "terraform.tfstate.backup",
            "tofu.tfstate",
            "tofu.tfstate.backup",
        ]
        state_present = any(os.path.exists(path) for path in state_files)
        if state_present:
            return True, None
        return None, None

    def _get_state_summary(self) -> Tuple[Optional[bool], Optional[int]]:
        try:
            result = subprocess.run(
                [self.tool_name, "state", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:
            return None, None

        if result.returncode == 0:
            resources = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return True, len(resources)

        error_text = f"{result.stdout}\n{result.stderr}".lower()
        if "no state" in error_text or "state snapshot" in error_text:
            return False, 0

        return None, None

    def _evaluate_readiness(
        self,
        tf_file_count: int,
        initialized: bool,
        backend_configured: bool,
        lock_file_present: bool,
        state_present: Optional[bool],
    ) -> Tuple[str, str, str]:
        if tf_file_count == 0:
            return (
                "empty",
                "No configuration detected",
                "Add .tf files or switch to an infrastructure workspace before running commands.",
            )

        if not initialized:
            return (
                "needs_init",
                "Initialization required",
                "Run `infra-guide init` before planning or applying changes.",
            )

        if not lock_file_present and not backend_configured:
            return (
                "partial",
                "Local-only prototype",
                "You can plan safely now, but add a lock file and remote backend before team use.",
            )

        if not backend_configured:
            return (
                "partial",
                "Ready for local workflows",
                "Planning is safe. Consider a remote backend if this stack is shared across environments.",
            )

        if state_present is False:
            return (
                "ready",
                "Ready to plan",
                "Backend and initialization look healthy. Run `infra-guide plan` to create the first stateful plan.",
            )

        return (
            "ready",
            "Ready to operate",
            "Environment looks healthy. Recommended flow: doctor, plan, then apply.",
        )
