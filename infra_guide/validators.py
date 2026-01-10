"""
Pre-flight validators - comprehensive checks before executing commands.
"""

import subprocess
import os
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


class PreFlightValidator:
    """Runs comprehensive pre-flight checks before infrastructure operations."""

    def __init__(self, tool_name: str):
        """
        Initialize validator.

        Args:
            tool_name: The IaC tool name ('terraform' or 'tofu')
        """
        self.tool_name = tool_name
        self.console = Console()

    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all pre-flight checks.

        Returns:
            Dict with check results
        """
        checks = [
            self._check_configuration_files(),
            self._check_initialization(),
            self._check_syntax(),
            self._check_formatting(),
            self._check_backend_config(),
            self._check_provider_versions(),
            self._check_required_variables()
        ]

        passed = sum(1 for check in checks if check["status"] == "pass")
        warnings = sum(1 for check in checks if check["status"] == "warning")
        failed = sum(1 for check in checks if check["status"] == "fail")

        return {
            "checks": checks,
            "total": len(checks),
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "all_passed": failed == 0
        }

    def _check_configuration_files(self) -> Dict[str, Any]:
        """Check if configuration files exist."""
        tf_files = [f for f in os.listdir('.') if f.endswith('.tf')]
        
        if tf_files:
            return {
                "name": "Configuration Files",
                "status": "pass",
                "message": f"Found {len(tf_files)} .tf file(s)"
            }
        else:
            return {
                "name": "Configuration Files",
                "status": "fail",
                "message": "No .tf files found in current directory"
            }

    def _check_initialization(self) -> Dict[str, Any]:
        """Check if directory is initialized."""
        if os.path.exists('.terraform'):
            return {
                "name": "Initialization",
                "status": "pass",
                "message": "Directory is initialized"
            }
        else:
            return {
                "name": "Initialization",
                "status": "warning",
                "message": "Directory not initialized - run 'init' first"
            }

    def _check_syntax(self) -> Dict[str, Any]:
        """Validate configuration syntax."""
        try:
            result = subprocess.run(
                [self.tool_name, "validate", "-json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {
                    "name": "Syntax Validation",
                    "status": "pass",
                    "message": "Configuration is valid"
                }
            else:
                return {
                    "name": "Syntax Validation",
                    "status": "fail",
                    "message": "Configuration has syntax errors"
                }

        except subprocess.TimeoutExpired:
            return {
                "name": "Syntax Validation",
                "status": "warning",
                "message": "Validation timed out"
            }
        except Exception as e:
            return {
                "name": "Syntax Validation",
                "status": "warning",
                "message": f"Could not validate: {str(e)}"
            }

    def _check_formatting(self) -> Dict[str, Any]:
        """Check if files are properly formatted."""
        try:
            result = subprocess.run(
                [self.tool_name, "fmt", "-check", "-recursive"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return {
                    "name": "Code Formatting",
                    "status": "pass",
                    "message": "All files are properly formatted"
                }
            else:
                return {
                    "name": "Code Formatting",
                    "status": "warning",
                    "message": "Some files need formatting (run 'fmt')"
                }

        except Exception:
            return {
                "name": "Code Formatting",
                "status": "warning",
                "message": "Could not check formatting"
            }

    def _check_backend_config(self) -> Dict[str, Any]:
        """Check backend configuration."""
        # Check for backend configuration in .tf files
        has_backend = False
        try:
            for filename in os.listdir('.'):
                if filename.endswith('.tf'):
                    with open(filename, 'r') as f:
                        content = f.read()
                        if 'backend' in content:
                            has_backend = True
                            break

            if has_backend:
                return {
                    "name": "Backend Configuration",
                    "status": "pass",
                    "message": "Backend configured"
                }
            else:
                return {
                    "name": "Backend Configuration",
                    "status": "warning",
                    "message": "No backend configured (using local state)"
                }

        except Exception:
            return {
                "name": "Backend Configuration",
                "status": "warning",
                "message": "Could not check backend configuration"
            }

    def _check_provider_versions(self) -> Dict[str, Any]:
        """Check if provider versions are locked."""
        if os.path.exists('.terraform.lock.hcl'):
            return {
                "name": "Provider Versions",
                "status": "pass",
                "message": "Provider versions are locked"
            }
        else:
            return {
                "name": "Provider Versions",
                "status": "warning",
                "message": "No lock file found - run 'init' to lock versions"
            }

    def _check_required_variables(self) -> Dict[str, Any]:
        """Check for required variables without defaults."""
        # This is a simplified check
        try:
            result = subprocess.run(
                [self.tool_name, "validate"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if "variable" in result.stderr.lower() and "required" in result.stderr.lower():
                return {
                    "name": "Required Variables",
                    "status": "warning",
                    "message": "Some required variables may not be set"
                }
            else:
                return {
                    "name": "Required Variables",
                    "status": "pass",
                    "message": "All required variables appear to be set"
                }

        except Exception:
            return {
                "name": "Required Variables",
                "status": "pass",
                "message": "Variable check skipped"
            }

    def show_validation_report(self, results: Dict[str, Any]):
        """
        Display validation results.

        Args:
            results: Validation results
        """
        self.console.print()

        # Summary
        total = results["total"]
        passed = results["passed"]
        warnings = results["warnings"]
        failed = results["failed"]

        if results["all_passed"]:
            summary_color = "green"
            summary_icon = "✅"
            summary_text = "All Checks Passed"
        elif failed > 0:
            summary_color = "red"
            summary_icon = "❌"
            summary_text = "Some Checks Failed"
        else:
            summary_color = "yellow"
            summary_icon = "⚠️"
            summary_text = "Passed with Warnings"

        summary = Panel(
            f"[bold {summary_color}]{summary_icon} {summary_text}[/bold {summary_color}]\n\n"
            f"[white]Passed: {passed}/{total}\n"
            f"Warnings: {warnings}/{total}\n"
            f"Failed: {failed}/{total}[/white]",
            title="Pre-Flight Validation Report",
            border_style=summary_color,
            box=box.ROUNDED
        )

        self.console.print(summary)
        self.console.print()

        # Detailed results
        table = Table(
            title="Check Details",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED
        )
        table.add_column("Check", width=25)
        table.add_column("Status", width=12)
        table.add_column("Message", width=50)

        status_styles = {
            "pass": ("✓", "green"),
            "warning": ("⚠", "yellow"),
            "fail": ("✗", "red")
        }

        for check in results["checks"]:
            icon, color = status_styles.get(check["status"], ("?", "white"))
            table.add_row(
                check["name"],
                f"[{color}]{icon} {check['status'].upper()}[/{color}]",
                check["message"]
            )

        self.console.print(table)
        self.console.print()

        if not results["all_passed"]:
            recommendation = Panel(
                "[yellow]💡 Recommendation: Address warnings and errors before proceeding with infrastructure changes.[/yellow]",
                border_style="yellow",
                box=box.ROUNDED
            )
            self.console.print(recommendation)
            self.console.print()
