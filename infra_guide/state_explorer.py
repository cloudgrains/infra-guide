"""
State explorer - interactive browser for Terraform/OpenTofu state files.
"""

import subprocess
import json
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box
from rich.syntax import Syntax


class StateExplorer:
    """Explores and displays state file contents."""

    def __init__(self, tool_name: str):
        """
        Initialize state explorer.

        Args:
            tool_name: The IaC tool name ('terraform' or 'tofu')
        """
        self.tool_name = tool_name
        self.console = Console()

    def get_state_data(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve state data.

        Returns:
            State data as dictionary or None if failed
        """
        try:
            result = subprocess.run(
                [self.tool_name, "show", "-json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            return None

        except Exception:
            return None

    def list_resources(self) -> List[Dict[str, str]]:
        """
        List all resources in state.

        Returns:
            List of resource information
        """
        try:
            result = subprocess.run(
                [self.tool_name, "state", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                resources = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        resources.append({
                            "address": line.strip(),
                            "type": line.split('.')[0] if '.' in line else "unknown"
                        })
                return resources
            return []

        except Exception:
            return []

    def show_resource_detail(self, resource_address: str) -> Optional[str]:
        """
        Get detailed information about a specific resource.

        Args:
            resource_address: The resource address (e.g., 'aws_instance.web')

        Returns:
            Resource details as a formatted string
        """
        try:
            result = subprocess.run(
                [self.tool_name, "state", "show", resource_address],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return result.stdout
            return None

        except Exception:
            return None

    def show_resource_detail_panel(self, resource_address: str):
        """Display detailed information for a specific resource."""
        self.console.print()

        detail = self.show_resource_detail(resource_address)

        if not detail:
            self.console.print(
                f"[bold red]ERROR Could not read resource: {resource_address}[/bold red]\n"
            )
            return

        syntax = Syntax(detail, "hcl", theme="ansi_dark", word_wrap=True)
        panel = Panel(
            syntax,
            title=f"Resource Detail: {resource_address}",
            border_style="cyan",
            box=box.ROUNDED,
        )
        self.console.print(panel)
        self.console.print()

    def show_state_overview(self):
        """Display an overview of the state file."""
        self.console.print()
        
        state_data = self.get_state_data()
        
        if not state_data:
            self.console.print("[bold red]❌ No state file found or failed to read state[/bold red]\n")
            return

        # Extract summary information
        resources = state_data.get("values", {}).get("root_module", {}).get("resources", [])
        
        # Count resources by type
        type_counts = {}
        for resource in resources:
            res_type = resource.get("type", "unknown")
            type_counts[res_type] = type_counts.get(res_type, 0) + 1

        # Summary panel
        summary = Panel(
            f"[bold cyan]📊 State File Overview[/bold cyan]\n\n"
            f"[white]Total Resources: {len(resources)}\n"
            f"Resource Types: {len(type_counts)}[/white]",
            border_style="cyan",
            box=box.ROUNDED
        )
        self.console.print(summary)
        self.console.print()

        # Resources by type table
        if type_counts:
            table = Table(
                title="Resources by Type",
                show_header=True,
                header_style="bold magenta",
                box=box.ROUNDED
            )
            table.add_column("Resource Type", style="cyan", width=40)
            table.add_column("Count", style="green", justify="right", width=10)

            for res_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                table.add_row(res_type, str(count))

            self.console.print(table)
            self.console.print()

    def show_resources_list(self):
        """Display a list of all resources."""
        self.console.print()
        
        resources = self.list_resources()
        
        if not resources:
            self.console.print("[bold yellow]⚠️  No resources found in state[/bold yellow]\n")
            return

        table = Table(
            title=f"📦 All Resources ({len(resources)})",
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED
        )
        table.add_column("#", style="dim", width=5, justify="right")
        table.add_column("Resource Address", style="green", width=60)
        table.add_column("Type", style="blue", width=30)

        for idx, resource in enumerate(resources[:50], 1):  # Show first 50
            table.add_row(
                str(idx),
                resource["address"],
                resource["type"]
            )

        self.console.print(table)
        
        if len(resources) > 50:
            self.console.print(f"\n[dim]... and {len(resources) - 50} more resources[/dim]")
        
        self.console.print()

    def show_resource_tree(self):
        """Display resources as a tree structure."""
        self.console.print()
        
        resources = self.list_resources()
        
        if not resources:
            self.console.print("[bold yellow]⚠️  No resources found in state[/bold yellow]\n")
            return

        # Build tree structure
        tree = Tree("🌳 [bold cyan]Infrastructure State[/bold cyan]")
        
        # Group by resource type
        by_type = {}
        for resource in resources:
            res_type = resource["type"]
            if res_type not in by_type:
                by_type[res_type] = []
            by_type[res_type].append(resource["address"])

        # Add to tree
        for res_type, addresses in sorted(by_type.items())[:20]:  # Show first 20 types
            type_branch = tree.add(f"[yellow]{res_type}[/yellow] ({len(addresses)})")
            for address in addresses[:10]:  # Show first 10 of each type
                type_branch.add(f"[green]{address}[/green]")
            if len(addresses) > 10:
                type_branch.add(f"[dim]... and {len(addresses) - 10} more[/dim]")

        self.console.print(tree)
        self.console.print()

    def get_state_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the state file.

        Returns:
            Dictionary with state statistics
        """
        resources = self.list_resources()
        state_data = self.get_state_data()

        stats = {
            "total_resources": len(resources),
            "resource_types": len(set(r["type"] for r in resources)),
            "has_state": state_data is not None
        }

        if state_data:
            stats["terraform_version"] = state_data.get("terraform_version", "unknown")
            
        return stats
