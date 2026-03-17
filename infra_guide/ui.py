"""
UI components for the infra-guide terminal experience.
"""

import shlex
from typing import Any, Dict, List, Optional

from rich import box
from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from infra_guide import __version__


RISK_STYLE = {
    "low": ("LOW", "green"),
    "medium": ("MEDIUM", "yellow"),
    "high": ("HIGH", "red"),
}

READINESS_STYLE = {
    "ready": ("READY", "green"),
    "partial": ("PARTIAL", "yellow"),
    "needs_init": ("NEEDS INIT", "yellow"),
    "empty": ("EMPTY", "red"),
}


class InfraGuideUI:
    """Handles all UI rendering using Rich."""

    def __init__(self, tool_name: str, tool_version: str, no_color: bool = False):
        self.console = Console(no_color=no_color)
        self.tool_name = tool_name
        self.tool_version = tool_version

    def clear_screen(self):
        """Clear the terminal screen."""
        self.console.clear()

    def show_banner(
        self, snapshot: Optional[Dict[str, Any]] = None, title: str = "Command Center"
    ):
        """Display the application banner."""
        heading = Text()
        heading.append("infra-guide", style="bold cyan")
        heading.append("  ")
        heading.append(title, style="bold white")
        heading.append(f"  v{__version__}", style="dim")

        lines = [
            f"Tool: {self.tool_name} ({self.tool_version})",
        ]

        if snapshot:
            lines.append(f"Workspace: {snapshot.get('workspace', 'unknown')}")
            lines.append(f"Directory: {snapshot.get('cwd', '.')}")

        banner = Panel(
            Group(heading, Text("\n".join(lines), style="white")),
            border_style="cyan",
            box=box.HEAVY,
            padding=(1, 2),
        )
        self.console.print(banner)

    def show_dashboard(self, snapshot: Dict[str, Any]):
        """Display a product-style overview of the current project."""
        self.show_banner(snapshot=snapshot)

        readiness_label, readiness_color = READINESS_STYLE.get(
            snapshot.get("readiness", "partial"),
            ("UNKNOWN", "white"),
        )

        overview = Table.grid(padding=(0, 1))
        overview.add_column(style="bold cyan", width=14)
        overview.add_column(style="white")
        overview.add_row("Workspace", snapshot.get("workspace", "unknown"))
        overview.add_row("Directory", snapshot.get("cwd", "."))
        overview.add_row("Readiness", f"[{readiness_color}]{readiness_label}[/{readiness_color}]")

        project = Table.grid(padding=(0, 1))
        project.add_column(style="bold cyan", width=14)
        project.add_column(style="white")
        project.add_row("Config files", str(snapshot.get("tf_file_count", 0)))
        project.add_row("Var files", str(snapshot.get("tfvars_file_count", 0)))
        project.add_row("Modules", str(snapshot.get("module_block_count", 0)))
        project.add_row(
            "Initialized",
            self._format_bool(snapshot.get("initialized")),
        )
        project.add_row(
            "Lock file",
            self._format_bool(snapshot.get("lock_file_present")),
        )
        project.add_row(
            "Backend",
            self._format_bool(snapshot.get("backend_configured")),
        )
        project.add_row(
            "State",
            self._format_state(snapshot.get("state_present"), snapshot.get("state_resource_count")),
        )

        next_step = Panel(
            Group(
                Text(snapshot.get("readiness_label", "Workspace status"), style="bold white"),
                Text(snapshot.get("recommendation", ""), style="white"),
                Text(
                    "\nRecommended flow: doctor -> init -> plan -> apply",
                    style="dim",
                ),
            ),
            title="[bold]Next Step[/bold]",
            border_style=readiness_color,
            box=box.ROUNDED,
            padding=(1, 2),
        )

        cards = Columns(
            [
                Panel(
                    overview,
                    title="[bold]Environment[/bold]",
                    border_style="blue",
                    box=box.ROUNDED,
                    padding=(1, 1),
                ),
                Panel(
                    project,
                    title="[bold]Project Signals[/bold]",
                    border_style="magenta",
                    box=box.ROUNDED,
                    padding=(1, 1),
                ),
                next_step,
            ],
            expand=True,
            equal=True,
        )
        self.console.print(cards)
        self.console.print(
            Panel(
                Text(
                    "Tip: run `infra-guide doctor`, `infra-guide guide plan`, or "
                    "`infra-guide plan --out tfplan` for direct workflows.",
                    style="dim",
                ),
                border_style="dim",
                box=box.ROUNDED,
                padding=(0, 1),
            )
        )
        self.console.print()

    def show_menu(self) -> str:
        """
        Display the main command palette and get user choice.

        Returns:
            str: User's menu choice
        """
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            style="white",
        )
        table.add_column("Key", style="bold yellow", width=6)
        table.add_column("Command", style="bold green", width=12)
        table.add_column("Purpose", style="white")
        table.add_column("Risk", justify="center", width=12)

        menu_items = [
            ("1", "doctor", "Workspace health check with guidance", "low"),
            ("2", "init", "Initialize providers, modules, and backend", "low"),
            ("3", "plan", "Preview infrastructure changes", "low"),
            ("4", "apply", "Apply changes to infrastructure", "medium"),
            ("5", "destroy", "Remove managed infrastructure", "high"),
            ("6", "validate", "Run pre-flight validations", "low"),
            ("7", "drift", "Detect drift from real infrastructure", "low"),
            ("8", "state", "Explore current state", "low"),
            ("9", "workspace", "Manage environments", "medium"),
            ("10", "fmt", "Format Terraform/OpenTofu files", "low"),
            ("11", "cicd", "Run non-interactive pipeline flow", "medium"),
            ("0", "exit", "Close infra-guide", "low"),
        ]

        for option, command, description, risk in menu_items:
            badge, color = RISK_STYLE.get(risk, ("INFO", "white"))
            table.add_row(option, command, description, f"[{color}]{badge}[/{color}]")

        menu_panel = Panel(
            table,
            title="[bold white]Command Palette[/bold white]",
            border_style="cyan",
            padding=(1, 2),
        )

        self.console.print(menu_panel)
        self.console.print()

        return Prompt.ask(
            "[bold cyan]Select an option[/bold cyan]",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "0"],
            default="0",
        )

    def show_guide(
        self,
        title: str,
        description: str,
        flags: List[Dict[str, str]],
        best_practices: List[str],
        warnings: List[str],
        risk_level: str = "low",
        examples: Optional[List[str]] = None,
    ):
        """
        Display a guide panel for a command.

        Args:
            title: Command title
            description: What the command does
            flags: List of common flags with descriptions
            best_practices: List of best practice tips
            warnings: List of warning messages
            risk_level: low, medium, or high
            examples: Optional usage examples
        """
        badge, color = RISK_STYLE.get(risk_level, ("INFO", "white"))
        self.console.print()
        self.console.print(
            Panel(
                Group(
                    Text(f"{title}", style="bold white"),
                    Text(description, style="white"),
                    Text(f"\nRisk: {badge}", style=f"bold {color}"),
                ),
                title="[bold]Command Guide[/bold]",
                border_style=color,
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        self.console.print()

        if flags:
            flags_table = Table(
                show_header=True,
                header_style="bold cyan",
                box=box.SIMPLE_HEAVY,
                style="white",
            )
            flags_table.add_column("Flag", style="yellow", width=24)
            flags_table.add_column("Description", style="white")

            for flag in flags:
                flags_table.add_row(flag["flag"], flag["description"])

            self.console.print(
                Panel(
                    flags_table,
                    title="[bold cyan]Useful Flags[/bold cyan]",
                    border_style="cyan",
                    box=box.ROUNDED,
                )
            )
            self.console.print()

        if examples:
            example_text = Text("\n".join(examples), style="white")
            self.console.print(
                Panel(
                    example_text,
                    title="[bold blue]Examples[/bold blue]",
                    border_style="blue",
                    box=box.ROUNDED,
                )
            )
            self.console.print()

        if best_practices:
            practices_text = Text()
            for index, practice in enumerate(best_practices, 1):
                practices_text.append(f"{index}. ", style="bold green")
                practices_text.append(f"{practice}\n", style="white")

            self.console.print(
                Panel(
                    practices_text,
                    title="[bold green]Best Practices[/bold green]",
                    border_style="green",
                    box=box.ROUNDED,
                )
            )
            self.console.print()

        if warnings:
            warning_text = Text()
            for warning in warnings:
                warning_text.append(f"- {warning}\n", style="yellow")

            self.console.print(
                Panel(
                    warning_text,
                    title="[bold yellow]Warnings[/bold yellow]",
                    border_style="yellow",
                    box=box.ROUNDED,
                )
            )
            self.console.print()

    def prompt_for_extra_args(self) -> List[str]:
        """Allow the user to add optional CLI flags before execution."""
        while True:
            raw_args = Prompt.ask(
                "[cyan]Optional extra flags (press Enter to skip)[/cyan]",
                default="",
            ).strip()

            if not raw_args:
                return []

            try:
                return shlex.split(raw_args)
            except ValueError as error:
                self.show_error(f"Could not parse flags: {error}")

    def show_command_preview(self, command: str, risk_level: str = "low"):
        """Display a command preview panel."""
        badge, color = RISK_STYLE.get(risk_level, ("INFO", "white"))
        self.console.print()
        self.console.print(
            Panel(
                Group(
                    Text(command, style="bold white"),
                    Text(f"Risk level: {badge}", style=f"bold {color}"),
                ),
                title="[bold]Command Preview[/bold]",
                border_style=color,
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        self.console.print()

    def confirm_execution(self, command: str, risk_level: str = "low") -> bool:
        """
        Ask user to confirm command execution.

        Args:
            command: The command to execute
            risk_level: low, medium, or high

        Returns:
            bool: True if user confirms, False otherwise
        """
        default_choice = risk_level == "low"
        return Confirm.ask(
            f"[bold yellow]Execute '{command}' now?[/bold yellow]",
            default=default_choice,
        )

    def show_command_output_header(self, command: str):
        """Display header before command execution."""
        self.console.print()
        header = Panel(
            Text(f"Executing: {command}", style="bold white"),
            style="bold blue",
            box=box.HEAVY,
            padding=(1, 2),
        )
        self.console.print(header)
        self.console.print()

    def show_project_status(self, snapshot: Dict[str, Any], title: str = "Project Status"):
        """Display a concise status report suitable for direct CLI commands."""
        readiness_label, readiness_color = READINESS_STYLE.get(
            snapshot.get("readiness", "partial"),
            ("UNKNOWN", "white"),
        )

        table = Table(show_header=False, box=box.SIMPLE_HEAVY, padding=(0, 1))
        table.add_column(style="bold cyan", width=18)
        table.add_column(style="white")
        table.add_row("Directory", snapshot.get("cwd", "."))
        table.add_row("Workspace", snapshot.get("workspace", "unknown"))
        table.add_row(
            "Readiness", f"[{readiness_color}]{readiness_label}[/{readiness_color}]"
        )
        table.add_row("Config files", str(snapshot.get("tf_file_count", 0)))
        table.add_row("Var files", str(snapshot.get("tfvars_file_count", 0)))
        table.add_row("Modules", str(snapshot.get("module_block_count", 0)))
        table.add_row("Initialized", self._format_bool(snapshot.get("initialized")))
        table.add_row("Lock file", self._format_bool(snapshot.get("lock_file_present")))
        table.add_row("Backend", self._format_bool(snapshot.get("backend_configured")))
        table.add_row(
            "State",
            self._format_state(snapshot.get("state_present"), snapshot.get("state_resource_count")),
        )

        self.console.print(
            Panel(
                Group(
                    table,
                    Text(f"\nRecommendation: {snapshot.get('recommendation', '')}", style="white"),
                ),
                title=f"[bold]{title}[/bold]",
                border_style=readiness_color,
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        self.console.print()

    def show_success(self, message: str):
        """Display success message."""
        self.console.print(f"\n[bold green]OK[/bold green] {message}\n")

    def show_error(self, message: str):
        """Display error message."""
        self.console.print(f"\n[bold red]ERROR[/bold red] {message}\n")

    def show_info(self, message: str):
        """Display info message."""
        self.console.print(f"\n[bold cyan]INFO[/bold cyan] {message}\n")

    def wait_for_enter(self):
        """Wait for user to press Enter."""
        self.console.print()
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

    def show_no_tool_error(self):
        """Display error when no tool is detected."""
        error_panel = Panel(
            Text.from_markup(
                "[bold red]No infrastructure tool found.[/bold red]\n\n"
                "[white]infra-guide requires either [bold green]Terraform[/bold green] "
                "or [bold green]OpenTofu[/bold green] in PATH.[/white]\n\n"
                "[cyan]Terraform:[/cyan] https://www.terraform.io/downloads\n"
                "[cyan]OpenTofu:[/cyan] https://opentofu.org/docs/intro/install/\n\n"
                "[dim]Install one of them and try again.[/dim]"
            ),
            border_style="red",
            box=box.HEAVY,
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(error_panel)
        self.console.print()

    def show_goodbye(self):
        """Display goodbye message."""
        goodbye = Panel(
            Text(
                "Thanks for using infra-guide.\nShip safe changes.",
                style="bold cyan",
                justify="center",
            ),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(goodbye)
        self.console.print()

    def _format_bool(self, value: Optional[bool]) -> str:
        if value is True:
            return "[green]YES[/green]"
        if value is False:
            return "[red]NO[/red]"
        return "[dim]UNKNOWN[/dim]"

    def _format_state(
        self, state_present: Optional[bool], state_resource_count: Optional[int]
    ) -> str:
        if state_present is True and state_resource_count is not None:
            return f"[green]AVAILABLE[/green] ({state_resource_count} resources)"
        if state_present is True:
            return "[green]AVAILABLE[/green]"
        if state_present is False:
            return "[yellow]NONE[/yellow]"
        return "[dim]UNKNOWN[/dim]"
