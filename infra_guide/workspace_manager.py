"""
Workspace manager for Terraform/OpenTofu environments.
"""

import subprocess
from typing import Any, Dict, List

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table


class WorkspaceManager:
    """Manages workspaces for multi-environment deployments."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.console = Console()

    def _run_workspace_command(self, args: List[str]) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                [self.tool_name, "workspace"] + args,
                capture_output=True,
                text=True,
                timeout=15,
            )
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        except Exception as error:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(error),
            }

    def list_workspaces(self) -> Dict[str, Any]:
        """
        List all workspaces.

        Returns:
            Dict with workspace list and current workspace
        """
        result = self._run_workspace_command(["list"])
        if not result["success"]:
            return {
                "success": False,
                "error": result["stderr"] or "Failed to list workspaces",
            }

        workspaces = []
        current = None

        for line in result["stdout"].splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue

            if cleaned.startswith("*"):
                current = cleaned.replace("*", "", 1).strip()
                workspaces.append(current)
            else:
                workspaces.append(cleaned)

        return {
            "success": True,
            "workspaces": workspaces,
            "current": current or "default",
            "count": len(workspaces),
        }

    def create_workspace(self, name: str) -> Dict[str, Any]:
        """Create a new workspace."""
        return self._run_workspace_command(["new", name])

    def select_workspace(self, name: str) -> Dict[str, Any]:
        """Switch to a different workspace."""
        return self._run_workspace_command(["select", name])

    def delete_workspace(self, name: str) -> Dict[str, Any]:
        """Delete a workspace."""
        return self._run_workspace_command(["delete", name])

    def show_workspace_overview(self) -> Dict[str, Any]:
        """Render a current workspace overview and return the raw data."""
        ws_info = self.list_workspaces()

        if not ws_info.get("success"):
            self.console.print(f"[bold red]ERROR[/bold red] {ws_info.get('error')}\n")
            return ws_info

        current = ws_info.get("current", "default")
        panel = Panel(
            f"[bold cyan]Current workspace:[/bold cyan] [bold green]{current}[/bold green]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        self.console.print(panel)
        self.console.print()

        table = Table(
            title=f"Workspaces ({ws_info.get('count', 0)})",
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
        )
        table.add_column("Workspace", style="green", width=30)
        table.add_column("Status", style="white", width=16)

        for workspace in ws_info.get("workspaces", []):
            status = "[green]CURRENT[/green]" if workspace == current else ""
            table.add_row(workspace, status)

        self.console.print(table)
        self.console.print()
        return ws_info

    def show_workspace_menu(self):
        """Display interactive workspace management menu."""
        while True:
            self.console.clear()
            self.console.print()

            ws_info = self.show_workspace_overview()
            if not ws_info.get("success"):
                Prompt.ask("[dim]Press Enter to return[/dim]", default="")
                return

            menu_table = Table(show_header=False, box=None, padding=(0, 2))
            menu_table.add_column(style="yellow", width=5)
            menu_table.add_column(style="white")
            menu_table.add_row("1", "Switch workspace")
            menu_table.add_row("2", "Create new workspace")
            menu_table.add_row("3", "Delete workspace")
            menu_table.add_row("4", "Refresh list")
            menu_table.add_row("5", "Back to main menu")

            self.console.print(menu_table)
            self.console.print()

            choice = Prompt.ask(
                "[bold cyan]Select an option[/bold cyan]",
                choices=["1", "2", "3", "4", "5"],
                default="5",
            )

            if choice == "1":
                self._handle_switch_workspace(ws_info.get("workspaces", []))
            elif choice == "2":
                self._handle_create_workspace()
            elif choice == "3":
                self._handle_delete_workspace(ws_info.get("workspaces", []), ws_info.get("current", "default"))
            elif choice == "4":
                continue
            else:
                break

    def _handle_switch_workspace(self, workspaces: List[str]):
        """Handle workspace switching."""
        if not workspaces:
            self.console.print("[yellow]No workspaces available.[/yellow]")
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            return

        self.console.print()
        self.console.print("[cyan]Available workspaces:[/cyan]")
        for index, workspace in enumerate(workspaces, 1):
            self.console.print(f"  {index}. {workspace}")

        self.console.print()
        workspace_name = Prompt.ask("[cyan]Enter workspace name[/cyan]")

        if workspace_name not in workspaces:
            self.console.print("[bold red]ERROR[/bold red] Workspace not found.")
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            return

        result = self.select_workspace(workspace_name)
        if result["success"]:
            self.console.print(
                f"[bold green]OK[/bold green] Switched to workspace: {workspace_name}"
            )
        else:
            self.console.print(
                f"[bold red]ERROR[/bold red] {result['stderr'] or 'Failed to switch workspace.'}"
            )

        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

    def _handle_create_workspace(self):
        """Handle workspace creation."""
        self.console.print()
        workspace_name = Prompt.ask("[cyan]Enter new workspace name[/cyan]").strip()

        if not workspace_name:
            self.console.print("[yellow]Workspace name cannot be empty.[/yellow]")
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            return

        result = self.create_workspace(workspace_name)
        if result["success"]:
            self.console.print(
                f"[bold green]OK[/bold green] Created workspace: {workspace_name}"
            )
        else:
            self.console.print(
                f"[bold red]ERROR[/bold red] {result['stderr'] or 'Failed to create workspace.'}"
            )

        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

    def _handle_delete_workspace(self, workspaces: List[str], current: str):
        """Handle workspace deletion."""
        deletable = [workspace for workspace in workspaces if workspace != current]

        if not deletable:
            self.console.print(
                "[yellow]No workspaces available to delete. The current workspace cannot be deleted.[/yellow]"
            )
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            return

        self.console.print()
        self.console.print("[cyan]Deletable workspaces:[/cyan]")
        for index, workspace in enumerate(deletable, 1):
            self.console.print(f"  {index}. {workspace}")

        self.console.print()
        workspace_name = Prompt.ask("[cyan]Enter workspace name to delete[/cyan]").strip()

        if workspace_name not in deletable:
            self.console.print(
                "[bold red]ERROR[/bold red] Invalid workspace or current workspace selected."
            )
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            return

        if not Confirm.ask(
            f"[bold yellow]Delete workspace '{workspace_name}'?[/bold yellow]",
            default=False,
        ):
            self.console.print("[cyan]Deletion cancelled.[/cyan]")
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            return

        result = self.delete_workspace(workspace_name)
        if result["success"]:
            self.console.print(
                f"[bold green]OK[/bold green] Deleted workspace: {workspace_name}"
            )
        else:
            self.console.print(
                f"[bold red]ERROR[/bold red] {result['stderr'] or 'Failed to delete workspace.'}"
            )

        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
