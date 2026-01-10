"""
Workspace manager - manages Terraform/OpenTofu workspaces.
"""

import subprocess
from typing import List, Dict, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.prompt import Prompt, Confirm


class WorkspaceManager:
    """Manages workspaces for multi-environment deployments."""

    def __init__(self, tool_name: str):
        """
        Initialize workspace manager.

        Args:
            tool_name: The IaC tool name ('terraform' or 'tofu')
        """
        self.tool_name = tool_name
        self.console = Console()

    def list_workspaces(self) -> Dict[str, Any]:
        """
        List all workspaces.

        Returns:
            Dict with workspace list and current workspace
        """
        try:
            result = subprocess.run(
                [self.tool_name, "workspace", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                workspaces = []
                current = None
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line:
                        if line.startswith('*'):
                            # Current workspace
                            current = line.replace('*', '').strip()
                            workspaces.append(current)
                        else:
                            workspaces.append(line)

                return {
                    "success": True,
                    "workspaces": workspaces,
                    "current": current,
                    "count": len(workspaces)
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to list workspaces"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing workspaces: {str(e)}"
            }

    def create_workspace(self, name: str) -> bool:
        """
        Create a new workspace.

        Args:
            name: Workspace name

        Returns:
            True if successful
        """
        try:
            result = subprocess.run(
                [self.tool_name, "workspace", "new", name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0

        except Exception:
            return False

    def select_workspace(self, name: str) -> bool:
        """
        Switch to a different workspace.

        Args:
            name: Workspace name

        Returns:
            True if successful
        """
        try:
            result = subprocess.run(
                [self.tool_name, "workspace", "select", name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0

        except Exception:
            return False

    def delete_workspace(self, name: str) -> bool:
        """
        Delete a workspace.

        Args:
            name: Workspace name

        Returns:
            True if successful
        """
        try:
            result = subprocess.run(
                [self.tool_name, "workspace", "delete", name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0

        except Exception:
            return False

    def show_workspace_menu(self):
        """Display interactive workspace management menu."""
        while True:
            self.console.clear()
            self.console.print()
            
            # Get workspace info
            ws_info = self.list_workspaces()
            
            if not ws_info.get("success"):
                self.console.print(f"[bold red]❌ {ws_info.get('error')}[/bold red]\n")
                Prompt.ask("[dim]Press Enter to return[/dim]", default="")
                return

            # Show current workspace
            current = ws_info.get("current", "unknown")
            panel = Panel(
                f"[bold cyan]Current Workspace:[/bold cyan] [bold green]{current}[/bold green]",
                border_style="cyan",
                box=box.ROUNDED
            )
            self.console.print(panel)
            self.console.print()

            # Show workspace list
            table = Table(
                title=f"📁 Workspaces ({ws_info.get('count', 0)})",
                show_header=True,
                header_style="bold magenta",
                box=box.ROUNDED
            )
            table.add_column("Workspace", style="cyan", width=30)
            table.add_column("Status", style="green", width=15)

            for ws in ws_info.get("workspaces", []):
                status = "✓ Current" if ws == current else ""
                table.add_row(ws, status)

            self.console.print(table)
            self.console.print()

            # Menu options
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
                default="5"
            )

            if choice == "1":
                self._handle_switch_workspace(ws_info.get("workspaces", []))
            elif choice == "2":
                self._handle_create_workspace()
            elif choice == "3":
                self._handle_delete_workspace(ws_info.get("workspaces", []), current)
            elif choice == "4":
                continue
            elif choice == "5":
                break

    def _handle_switch_workspace(self, workspaces: List[str]):
        """Handle workspace switching."""
        if not workspaces:
            self.console.print("[yellow]No workspaces available[/yellow]")
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            return

        self.console.print()
        self.console.print("[cyan]Available workspaces:[/cyan]")
        for idx, ws in enumerate(workspaces, 1):
            self.console.print(f"  {idx}. {ws}")
        
        self.console.print()
        ws_name = Prompt.ask("[cyan]Enter workspace name[/cyan]")
        
        if ws_name in workspaces:
            if self.select_workspace(ws_name):
                self.console.print(f"[bold green]✅ Switched to workspace: {ws_name}[/bold green]")
            else:
                self.console.print(f"[bold red]❌ Failed to switch to workspace: {ws_name}[/bold red]")
        else:
            self.console.print("[bold red]❌ Workspace not found[/bold red]")
        
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

    def _handle_create_workspace(self):
        """Handle workspace creation."""
        self.console.print()
        ws_name = Prompt.ask("[cyan]Enter new workspace name[/cyan]")
        
        if ws_name:
            if self.create_workspace(ws_name):
                self.console.print(f"[bold green]✅ Created and switched to workspace: {ws_name}[/bold green]")
            else:
                self.console.print(f"[bold red]❌ Failed to create workspace: {ws_name}[/bold red]")
        
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

    def _handle_delete_workspace(self, workspaces: List[str], current: str):
        """Handle workspace deletion."""
        deletable = [ws for ws in workspaces if ws != current]
        
        if not deletable:
            self.console.print("[yellow]No workspaces available to delete (cannot delete current workspace)[/yellow]")
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            return

        self.console.print()
        self.console.print("[cyan]Deletable workspaces:[/cyan]")
        for idx, ws in enumerate(deletable, 1):
            self.console.print(f"  {idx}. {ws}")
        
        self.console.print()
        ws_name = Prompt.ask("[cyan]Enter workspace name to delete[/cyan]")
        
        if ws_name in deletable:
            if Confirm.ask(f"[bold yellow]⚠️  Delete workspace '{ws_name}'?[/bold yellow]", default=False):
                if self.delete_workspace(ws_name):
                    self.console.print(f"[bold green]✅ Deleted workspace: {ws_name}[/bold green]")
                else:
                    self.console.print(f"[bold red]❌ Failed to delete workspace: {ws_name}[/bold red]")
        else:
            self.console.print("[bold red]❌ Invalid workspace or cannot delete current workspace[/bold red]")
        
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
