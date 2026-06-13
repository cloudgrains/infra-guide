"""
Drift detection module - detects changes between state and actual infrastructure.
"""

import subprocess
import json
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


class DriftDetector:
    """Detects infrastructure drift."""

    def __init__(self, tool_name: str):
        """
        Initialize drift detector.

        Args:
            tool_name: The IaC tool name ('terraform' or 'tofu')
        """
        self.tool_name = tool_name
        self.console = Console()

    def detect_drift(self) -> Dict[str, Any]:
        """
        Detect drift by running a refresh-only plan.

        Returns:
            Dict containing drift information
        """
        try:
            # Run plan with -refresh-only to detect drift
            result = subprocess.run(
                [self.tool_name, "plan", "-refresh-only", "-json"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "Failed to detect drift",
                    "details": result.stderr,
                }

            # Parse JSON output
            drift_items = []
            for line in result.stdout.split("\n"):
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("type") == "resource_drift":
                            drift_items.append(data.get("change", {}))
                    except json.JSONDecodeError:
                        continue

            return {
                "success": True,
                "drift_detected": len(drift_items) > 0,
                "drift_count": len(drift_items),
                "drifted_resources": drift_items,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Drift detection timed out"}
        except Exception as e:
            return {"success": False, "error": f"Drift detection failed: {str(e)}"}

    def show_drift_report(self, drift_data: Dict[str, Any]):
        """
        Display a formatted drift report.

        Args:
            drift_data: Drift detection results
        """
        if not drift_data.get("success"):
            self.console.print(f"\n[bold red]❌ {drift_data.get('error')}[/bold red]\n")
            return

        if not drift_data.get("drift_detected"):
            panel = Panel(
                "[bold green]✅ No drift detected![/bold green]\n\n"
                "[white]Your infrastructure matches the state file.[/white]",
                title="Drift Detection Report",
                border_style="green",
                box=box.ROUNDED,
            )
            self.console.print(panel)
            return

        # Show drifted resources
        drift_count = drift_data.get("drift_count", 0)

        table = Table(
            title=f"⚠️  Detected {drift_count} Drifted Resource(s)",
            show_header=True,
            header_style="bold yellow",
            box=box.ROUNDED,
        )
        table.add_column("Resource", style="cyan", width=40)
        table.add_column("Action", style="yellow", width=15)
        table.add_column("Status", style="white")

        for resource in drift_data.get("drifted_resources", [])[:10]:  # Show first 10
            addr = resource.get("resource", {}).get("addr", "Unknown")
            action = resource.get("action", "unknown")

            action_emoji = {"update": "🔄", "delete": "🗑️", "create": "➕", "no-op": "✓"}.get(
                action, "❓"
            )

            table.add_row(addr, f"{action_emoji} {action}", "Drift Detected")

        self.console.print()
        self.console.print(table)
        self.console.print()

        warning_panel = Panel(
            "[yellow]⚠️  Infrastructure has drifted from the state file!\n\n"
            "This means changes were made outside of Terraform/OpenTofu.\n"
            "Consider running 'apply' to bring infrastructure back in sync.[/yellow]",
            border_style="yellow",
            box=box.ROUNDED,
        )
        self.console.print(warning_panel)
        self.console.print()
