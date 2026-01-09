"""
Detects whether terraform or tofu is installed on the system.
"""

import shutil
from typing import Optional


class ToolDetector:
    """Detects available IaC tools (terraform or tofu)."""

    @staticmethod
    def detect() -> Optional[str]:
        """
        Detect which tool is available.

        Returns:
            str: 'tofu' if OpenTofu is installed, 'terraform' if Terraform is installed
            None: if neither is installed
        """
        # Check for tofu first (prefer OpenTofu)
        if shutil.which("tofu"):
            return "tofu"
        
        # Fall back to terraform
        if shutil.which("terraform"):
            return "terraform"
        
        return None

    @staticmethod
    def get_version(tool: str) -> str:
        """
        Get the version of the detected tool.

        Args:
            tool: The tool name ('tofu' or 'terraform')

        Returns:
            str: Version string or 'unknown'
        """
        import subprocess

        try:
            result = subprocess.run(
                [tool, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Extract first line which typically contains version
                return result.stdout.split('\n')[0].strip()
            return "unknown"
        except Exception:
            return "unknown"
