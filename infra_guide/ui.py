"""
UI components for the infra-guide TUI.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.text import Text
from rich import box
from typing import List, Dict, Any


class InfraGuideUI:
    """Handles all UI rendering using rich library."""

    def __init__(self, tool_name: str, tool_version: str):
        """
        Initialize the UI.

        Args:
            tool_name: Name of the detected tool ('tofu' or 'terraform')
            tool_version: Version string of the tool
        """
        self.console = Console()
        self.tool_name = tool_name
        self.tool_version = tool_version

    def clear_screen(self):
        """Clear the terminal screen."""
        self.console.clear()

    def show_banner(self):
        """Display the application banner."""
        banner_text = Text()
        banner_text.append("🚀 ", style="bold yellow")
        banner_text.append("infra-guide", style="bold cyan")
        banner_text.append(" - Interactive Infrastructure Guide", style="bold white")
        
        info_text = Text()
        info_text.append(f"\n📦 Using: ", style="dim")
        info_text.append(f"{self.tool_name}", style="bold green")
        info_text.append(f" ({self.tool_version})", style="dim")

        banner = Panel(
            banner_text + info_text,
            box=box.DOUBLE,
            style="bold blue",
            padding=(1, 2)
        )
        self.console.print(banner)

    def show_menu(self) -> str:
        """
        Display the main menu and get user choice.

        Returns:
            str: User's menu choice
        """
        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            style="cyan"
        )
        table.add_column("Option", style="bold yellow", width=8)
        table.add_column("Command", style="bold green", width=12)
        table.add_column("Description", style="white")

        menu_items = [
            ("1", "init", "🔧 Initialize a working directory"),
            ("2", "plan", "📋 Show changes required by current configuration"),
            ("3", "apply", "✅ Create or update infrastructure"),
            ("4", "destroy", "💥 Destroy previously-created infrastructure"),
            ("5", "exit", "🚪 Exit infra-guide"),
        ]

        for option, command, description in menu_items:
            table.add_row(option, command, description)

        menu_panel = Panel(
            table,
            title="[bold white]Main Menu[/bold white]",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(menu_panel)
        self.console.print()

        choice = Prompt.ask(
            "[bold cyan]Select an option[/bold cyan]",
            choices=["1", "2", "3", "4", "5"],
            default="5"
        )
        return choice

    def show_guide(self, title: str, description: str, flags: List[Dict[str, str]], 
                   best_practices: List[str], warnings: List[str]):
        """
        Display a guide panel for a command.

        Args:
            title: Command title
            description: What the command does
            flags: List of common flags with descriptions
            best_practices: List of best practice tips
            warnings: List of warning messages
        """
        self.console.print()
        
        # Description panel
        desc_panel = Panel(
            Text(description, style="white"),
            title=f"[bold green]📖 What does '{title}' do?[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(desc_panel)
        self.console.print()

        # Flags table
        if flags:
            flags_table = Table(
                show_header=True,
                header_style="bold cyan",
                box=box.SIMPLE,
                style="white"
            )
            flags_table.add_column("Flag", style="yellow", width=25)
            flags_table.add_column("Description", style="white")

            for flag in flags:
                flags_table.add_row(flag["flag"], flag["description"])

            flags_panel = Panel(
                flags_table,
                title="[bold cyan]🎯 Common Flags[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED
            )
            self.console.print(flags_panel)
            self.console.print()

        # Best practices
        if best_practices:
            practices_text = Text()
            for i, practice in enumerate(best_practices, 1):
                practices_text.append(f"{i}. ", style="bold green")
                practices_text.append(f"{practice}\n", style="white")

            practices_panel = Panel(
                practices_text,
                title="[bold green]✨ Best Practices[/bold green]",
                border_style="green",
                box=box.ROUNDED
            )
            self.console.print(practices_panel)
            self.console.print()

        # Warnings
        if warnings:
            warnings_text = Text()
            for warning in warnings:
                warnings_text.append("⚠️  ", style="bold yellow")
                warnings_text.append(f"{warning}\n", style="yellow")

            warnings_panel = Panel(
                warnings_text,
                title="[bold yellow]⚠️  Important Warnings[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED
            )
            self.console.print(warnings_panel)
            self.console.print()

    def confirm_execution(self, command: str) -> bool:
        """
        Ask user to confirm command execution.

        Args:
            command: The command to execute

        Returns:
            bool: True if user confirms, False otherwise
        """
        self.console.print()
        return Confirm.ask(
            f"[bold yellow]Execute '{command}' now?[/bold yellow]",
            default=False
        )

    def show_command_output_header(self, command: str):
        """Display header before command execution."""
        self.console.print()
        header = Panel(
            Text(f"Executing: {command}", style="bold white"),
            style="bold blue",
            box=box.DOUBLE
        )
        self.console.print(header)
        self.console.print()

    def show_success(self, message: str):
        """Display success message."""
        self.console.print(f"\n[bold green]✅ {message}[/bold green]\n")

    def show_error(self, message: str):
        """Display error message."""
        self.console.print(f"\n[bold red]❌ {message}[/bold red]\n")

    def show_info(self, message: str):
        """Display info message."""
        self.console.print(f"\n[bold cyan]ℹ️  {message}[/bold cyan]\n")

    def wait_for_enter(self):
        """Wait for user to press Enter."""
        self.console.print()
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

    def show_no_tool_error(self):
        """Display error when no tool is detected."""
        error_panel = Panel(
            Text.from_markup(
                "[bold red]❌ Error: No Infrastructure Tool Found[/bold red]\n\n"
                "[white]infra-guide requires either [bold green]Terraform[/bold green] "
                "or [bold green]OpenTofu[/bold green] to be installed.\n\n"
                "Please install one of the following:[/white]\n\n"
                "[cyan]• Terraform:[/cyan] https://www.terraform.io/downloads\n"
                "[cyan]• OpenTofu:[/cyan] https://opentofu.org/docs/intro/install/\n\n"
                "[dim]After installation, make sure the command is in your PATH.[/dim]"
            ),
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        self.console.print()
        self.console.print(error_panel)
        self.console.print()

    def show_goodbye(self):
        """Display goodbye message."""
        goodbye = Panel(
            Text("👋 Thank you for using infra-guide!\nHappy infrastructure coding! 🚀", 
                 style="bold cyan", justify="center"),
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2)
        )
        self.console.print()
        self.console.print(goodbye)
        self.console.print()
