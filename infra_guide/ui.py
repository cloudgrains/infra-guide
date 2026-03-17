"""
UI components for the infra-guide terminal experience.
"""

import shlex
from typing import Any, Dict, List, Optional

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from infra_guide import __version__
from infra_guide.logo import LogoRenderer
from infra_guide.preferences import DEFAULT_THEME, THEMES, get_theme_palette


RISK_STYLE = {
    "low": ("LOW", "success"),
    "medium": ("MEDIUM", "warning"),
    "high": ("HIGH", "danger"),
}

READINESS_STYLE = {
    "ready": ("READY", "success"),
    "partial": ("PARTIAL", "warning"),
    "needs_init": ("NEEDS INIT", "warning"),
    "empty": ("EMPTY", "danger"),
}

STATUS_STYLE = {
    "info": "info",
    "success": "success",
    "warning": "warning",
    "danger": "danger",
}


class InfraGuideUI:
    """Handles all UI rendering using Rich."""

    def __init__(
        self,
        tool_name: str,
        tool_version: str,
        no_color: bool = False,
        theme_name: str = DEFAULT_THEME,
    ):
        self.console = Console(no_color=no_color)
        self.no_color = no_color
        self.tool_name = tool_name
        self.tool_version = tool_version
        self.theme_name = DEFAULT_THEME
        self.palette = get_theme_palette(DEFAULT_THEME)
        self.show_logo = False
        self.logo_renderer = LogoRenderer(no_color=no_color)
        self.set_theme(theme_name)

    def set_theme(self, theme_name: str):
        """Apply a different palette for the current session."""
        self.theme_name = theme_name if theme_name in THEMES else DEFAULT_THEME
        self.palette = get_theme_palette(self.theme_name)

    def set_logo_visibility(self, enabled: bool):
        """Enable or disable the interactive logo."""
        self.show_logo = enabled

    def clear_screen(self):
        """Clear the terminal screen."""
        self.console.clear()

    def show_banner(
        self, snapshot: Optional[Dict[str, Any]] = None, title: str = "Command Center"
    ):
        """Display the application banner."""
        hero = Text()
        hero.append("infra-guide", style=f"bold {self._color('brand')}")
        hero.append("  ")
        hero.append(title, style=f"bold {self._color('text')}")
        hero.append(f"  v{__version__}", style=self._muted_style())

        meta = Table.grid(expand=True)
        meta.add_column(ratio=1)
        meta.add_column(ratio=1)
        meta.add_column(ratio=1)
        meta.add_column(ratio=1)
        meta.add_row(
            self._chip("Tool", self.tool_name),
            self._chip("Version", self.tool_version),
            self._chip("Theme", THEMES[self.theme_name]["label"]),
            self._chip(
                "Workspace",
                snapshot.get("workspace", "unknown") if snapshot else "unknown",
            ),
        )

        subtitle = (
            Text(snapshot.get("cwd", "."), style=self._muted_style())
            if snapshot
            else Text("Interactive infrastructure guide", style=self._muted_style())
        )

        body = Group(hero, subtitle, Text(""), meta)
        if self.show_logo and not self.no_color:
            logo_width = self._logo_width()
            logo = self.logo_renderer.render(max_width=logo_width)
            if logo is not None:
                body = Columns(
                    [
                        Panel(
                            Align.center(logo, vertical="middle"),
                            border_style=self._color("surface_alt"),
                            box=box.ROUNDED,
                            padding=(0, 1),
                            width=logo_width + 6,
                        ),
                        body,
                    ],
                    expand=True,
                    equal=False,
                )

        self.console.print(
            Panel(
                body,
                border_style=self._color("surface"),
                box=box.HEAVY,
                padding=(1, 2),
            )
        )

    def show_dashboard(
        self,
        snapshot: Dict[str, Any],
        history_entries: Optional[List[Dict[str, Any]]] = None,
        favorites: Optional[List[Dict[str, Any]]] = None,
    ):
        """Display a modern dashboard for the interactive home screen."""
        history_entries = history_entries or []
        favorites = favorites or []

        self.show_banner(snapshot=snapshot)

        readiness_label, readiness_token = READINESS_STYLE.get(
            snapshot.get("readiness", "partial"),
            ("UNKNOWN", "info"),
        )

        stats = [
            self._metric_panel(
                "Readiness",
                readiness_label,
                snapshot.get("readiness_label", "Workspace status"),
                readiness_token,
            ),
            self._metric_panel(
                "Config",
                str(snapshot.get("tf_file_count", 0)),
                f"{snapshot.get('module_block_count', 0)} modules, {snapshot.get('tfvars_file_count', 0)} var files",
                "accent",
            ),
            self._metric_panel(
                "State",
                self._plain_state(snapshot.get("state_present"), snapshot.get("state_resource_count")),
                "Known infrastructure inventory",
                "surface_alt",
            ),
            self._metric_panel(
                "Guardrails",
                self._plain_guardrail(snapshot),
                "Init, backend, and lock status",
                "brand",
            ),
        ]
        self.console.print(Columns(stats, expand=True, equal=True))
        self.console.print()

        next_step = Panel(
            Group(
                Text(snapshot.get("readiness_label", "Workspace status"), style=f"bold {self._color('text')}"),
                Text(snapshot.get("recommendation", ""), style=self._base_style()),
                Text(
                    "\nSuggested flow: doctor -> plan --out tfplan -> apply --plan-file tfplan",
                    style=self._muted_style(),
                ),
            ),
            title=f"[bold {self._color('accent')}]Next Step[/bold {self._color('accent')}]",
            border_style=self._color("accent"),
            box=box.ROUNDED,
            padding=(1, 2),
        )

        recent_panel = self._history_panel(history_entries[:6], "Recent Commands")
        favorites_panel = self._favorites_panel(favorites[:6])

        self.console.print(Columns([next_step, recent_panel, favorites_panel], expand=True, equal=True))
        self.console.print()
        self.console.print(
            Panel(
                Text(
                    "Fresh in this TUI: theme switching, command history, favorites, and pre-apply cost insight.",
                    style=self._muted_style(),
                ),
                border_style=self._color("surface_alt"),
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
            header_style=f"bold {self._color('accent')}",
            box=box.SIMPLE_HEAVY,
            style=self._base_style(),
        )
        table.add_column("Key", style=f"bold {self._color('brand')}", width=6)
        table.add_column("Command", style=f"bold {self._color('accent_alt')}", width=14)
        table.add_column("Purpose", style=self._base_style())
        table.add_column("Risk", justify="center", width=12)

        menu_items = [
            ("1", "doctor", "Workspace health checks and recommendations", "low"),
            ("2", "init", "Initialize providers, modules, and backend", "low"),
            ("3", "plan", "Preview changes and save plans", "low"),
            ("4", "apply", "Apply changes with preflight cost insight", "medium"),
            ("5", "destroy", "Remove managed infrastructure", "high"),
            ("6", "validate", "Run pre-flight validations", "low"),
            ("7", "drift", "Detect drift from real infrastructure", "low"),
            ("8", "state", "Explore live state overview and resources", "low"),
            ("9", "workspace", "Manage environments and workspaces", "medium"),
            ("10", "history", "View history, favorites, and rerun commands", "low"),
            ("11", "theme", "Change the interface theme", "low"),
            ("12", "fmt", "Format Terraform/OpenTofu files", "low"),
            ("13", "cicd", "Run pipeline-friendly init/validate/plan flow", "medium"),
            ("0", "exit", "Close infra-guide", "low"),
        ]

        for option, command, description, risk in menu_items:
            badge, token = RISK_STYLE.get(risk, ("INFO", "info"))
            table.add_row(option, command, description, self._status_badge(badge, token))

        self.console.print(
            Panel(
                table,
                title=f"[bold {self._color('brand')}]Command Palette[/bold {self._color('brand')}]",
                border_style=self._color("surface"),
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        self.console.print()

        return Prompt.ask(
            f"[bold {self._color('accent')}]Select an option[/bold {self._color('accent')}]",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "0"],
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
        """
        badge, token = RISK_STYLE.get(risk_level, ("INFO", "info"))
        accent_color = self._color(token)
        self.console.print()
        self.console.print(
            Panel(
                Group(
                    Text(title, style=f"bold {self._color('text')}"),
                    Text(description, style=self._base_style()),
                    Text(f"\nRisk: {badge}", style=f"bold {accent_color}"),
                ),
                title=f"[bold {self._color('brand')}]Command Guide[/bold {self._color('brand')}]",
                border_style=accent_color,
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        self.console.print()

        if flags:
            flags_table = Table(
                show_header=True,
                header_style=f"bold {self._color('accent')}",
                box=box.SIMPLE_HEAVY,
                style=self._base_style(),
            )
            flags_table.add_column("Flag", style=f"bold {self._color('accent_alt')}", width=24)
            flags_table.add_column("Description", style=self._base_style())

            for flag in flags:
                flags_table.add_row(flag["flag"], flag["description"])

            self.console.print(
                Panel(
                    flags_table,
                    title=f"[bold {self._color('accent')}]Useful Flags[/bold {self._color('accent')}]",
                    border_style=self._color("accent"),
                    box=box.ROUNDED,
                )
            )
            self.console.print()

        if examples:
            example_text = Text("\n".join(examples), style=self._base_style())
            self.console.print(
                Panel(
                    example_text,
                    title=f"[bold {self._color('surface_alt')}]Examples[/bold {self._color('surface_alt')}]",
                    border_style=self._color("surface_alt"),
                    box=box.ROUNDED,
                )
            )
            self.console.print()

        if best_practices:
            practices_text = Text()
            for index, practice in enumerate(best_practices, 1):
                practices_text.append(f"{index}. ", style=f"bold {self._color('success')}")
                practices_text.append(f"{practice}\n", style=self._base_style())

            self.console.print(
                Panel(
                    practices_text,
                    title=f"[bold {self._color('success')}]Best Practices[/bold {self._color('success')}]",
                    border_style=self._color("success"),
                    box=box.ROUNDED,
                )
            )
            self.console.print()

        if warnings:
            warning_text = Text()
            for warning in warnings:
                warning_text.append(f"- {warning}\n", style=f"{self._color('warning')}")

            self.console.print(
                Panel(
                    warning_text,
                    title=f"[bold {self._color('warning')}]Warnings[/bold {self._color('warning')}]",
                    border_style=self._color("warning"),
                    box=box.ROUNDED,
                )
            )
            self.console.print()

    def prompt_for_extra_args(self) -> List[str]:
        """Allow the user to add optional CLI flags before execution."""
        while True:
            raw_args = Prompt.ask(
                f"[{self._color('accent')}]Optional extra flags (press Enter to skip)[/{self._color('accent')}]",
                default="",
            ).strip()

            if not raw_args:
                return []

            try:
                return shlex.split(raw_args)
            except ValueError as error:
                self.show_error(f"Could not parse flags: {error}")

    def show_command_preview(
        self, command: str, risk_level: str = "low", is_favorite: bool = False
    ):
        """Display a command preview panel."""
        badge, token = RISK_STYLE.get(risk_level, ("INFO", "info"))
        favorite_label = "Favorited" if is_favorite else "Not favorited"
        favorite_color = self._color("warning") if is_favorite else self._color("muted")
        self.console.print()
        self.console.print(
            Panel(
                Group(
                    Text(command, style=f"bold {self._color('text')}"),
                    Text(f"Risk level: {badge}", style=f"bold {self._color(token)}"),
                    Text(favorite_label, style=favorite_color),
                ),
                title=f"[bold {self._color('brand')}]Command Preview[/bold {self._color('brand')}]",
                border_style=self._color(token),
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        self.console.print()

    def prompt_favorite_action(self, is_favorite: bool) -> bool:
        """Ask whether the current preview should toggle favorite state."""
        if is_favorite:
            return Confirm.ask(
                f"[{self._color('warning')}]Remove this command from favorites?[/]",
                default=False,
            )
        return Confirm.ask(
            f"[{self._color('accent')}]Add this command to favorites for quick reuse?[/]",
            default=False,
        )

    def confirm_execution(self, command: str, risk_level: str = "low") -> bool:
        """Ask user to confirm command execution."""
        default_choice = risk_level == "low"
        return Confirm.ask(
            f"[bold {self._color('warning')}]Execute '{command}' now?[/bold {self._color('warning')}]",
            default=default_choice,
        )

    def show_command_output_header(self, command: str):
        """Display header before command execution."""
        self.console.print()
        self.console.print(
            Panel(
                Text(f"Executing: {command}", style=f"bold {self._color('text')}"),
                border_style=self._color("surface"),
                box=box.HEAVY,
                padding=(1, 2),
            )
        )
        self.console.print()

    def show_project_status(self, snapshot: Dict[str, Any], title: str = "Project Status"):
        """Display a concise status report suitable for direct CLI commands."""
        readiness_label, readiness_token = READINESS_STYLE.get(
            snapshot.get("readiness", "partial"),
            ("UNKNOWN", "info"),
        )

        table = Table(show_header=False, box=box.SIMPLE_HEAVY, padding=(0, 1))
        table.add_column(style=f"bold {self._color('accent')}", width=18)
        table.add_column(style=self._base_style())
        table.add_row("Directory", snapshot.get("cwd", "."))
        table.add_row("Workspace", snapshot.get("workspace", "unknown"))
        table.add_row(
            "Readiness", f"[{self._color(readiness_token)}]{readiness_label}[/{self._color(readiness_token)}]"
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
                    Rule(style=self._color("surface_alt")),
                    Text(f"Recommendation: {snapshot.get('recommendation', '')}", style=self._base_style()),
                ),
                title=f"[bold {self._color('brand')}]{title}[/bold {self._color('brand')}]",
                border_style=self._color(readiness_token),
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        self.console.print()

    def show_history_center(
        self,
        history_entries: List[Dict[str, Any]],
        favorites: List[Dict[str, Any]],
    ):
        """Render the history and favorites center."""
        self.console.print(
            Columns(
                [
                    self._history_panel(history_entries, "Recent Commands"),
                    self._favorites_panel(favorites),
                ],
                expand=True,
                equal=True,
            )
        )
        self.console.print()

    def show_theme_gallery(self, active_theme_name: str):
        """Display available themes."""
        panels = []
        for theme_name, data in THEMES.items():
            active = theme_name == active_theme_name
            title_color = self._color("success") if active else self._color("accent")
            body = Group(
                Text(data["label"], style=f"bold {data['brand']}"),
                Text(data["description"], style=self._muted_style()),
                Text(
                    "ACTIVE" if active else f"Use: {theme_name}",
                    style=f"bold {title_color}",
                ),
            )
            panels.append(
                Panel(
                    body,
                    title=f"[bold {title_color}]{theme_name}[/bold {title_color}]",
                    border_style=data["surface"],
                    box=box.ROUNDED,
                    padding=(1, 2),
                )
            )
        self.console.print(Columns(panels, expand=True, equal=True))
        self.console.print()

    def show_cost_preview(self, cost_data: Dict[str, Any]):
        """Display pre-apply cost insight."""
        status = cost_data.get("status", "info")
        token = STATUS_STYLE.get(status, "info")
        impact = str(cost_data.get("impact", "unknown")).upper()

        detail_text = Text()
        for line in cost_data.get("details", []):
            detail_text.append(f"- {line}\n", style=self._base_style())

        self.console.print(
            Panel(
                Group(
                    Text(cost_data.get("summary", ""), style=self._base_style()),
                    Text(
                        f"\nConfidence: {cost_data.get('confidence', 'low').upper()}  •  Impact: {impact}",
                        style=f"bold {self._color(token)}",
                    ),
                    Text(""),
                    detail_text,
                ),
                title=f"[bold {self._color(token)}]{cost_data.get('title', 'Cost Insight')}[/bold {self._color(token)}]",
                border_style=self._color(token),
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        self.console.print()

    def show_success(self, message: str):
        """Display success message."""
        self.console.print(f"\n[bold {self._color('success')}]OK[/bold {self._color('success')}] {message}\n")

    def show_error(self, message: str):
        """Display error message."""
        self.console.print(f"\n[bold {self._color('danger')}]ERROR[/bold {self._color('danger')}] {message}\n")

    def show_info(self, message: str):
        """Display info message."""
        self.console.print(f"\n[bold {self._color('info')}]INFO[/bold {self._color('info')}] {message}\n")

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
            border_style=self._color("danger"),
            box=box.HEAVY,
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(error_panel)
        self.console.print()

    def show_goodbye(self):
        """Display goodbye message."""
        self.console.print()
        self.console.print(
            Panel(
                Align.center(
                    Text(
                        "Thanks for using infra-guide.\nShip safe changes.",
                        style=f"bold {self._color('brand')}",
                    )
                ),
                border_style=self._color("surface"),
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        self.console.print()

    def _metric_panel(self, title: str, value: str, subtitle: str, token: str) -> Panel:
        return Panel(
            Group(
                Text(title, style=self._muted_style()),
                Text(str(value), style=f"bold {self._color(token)}"),
                Text(subtitle, style=self._muted_style()),
            ),
            border_style=self._color(token),
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def _history_panel(self, history_entries: List[Dict[str, Any]], title: str) -> Panel:
        if not history_entries:
            content = Text("No commands run yet in this profile.", style=self._muted_style())
        else:
            table = Table(show_header=True, box=box.SIMPLE, header_style=f"bold {self._color('accent')}")
            table.add_column("When", style=self._muted_style(), width=12)
            table.add_column("Command", style=self._base_style())
            table.add_column("Code", justify="right", width=6)
            for entry in history_entries:
                timestamp = entry.get("timestamp", "").split("T")[0]
                label = entry.get("label", entry.get("command_name", "command"))
                exit_code = str(entry.get("exit_code", "?"))
                table.add_row(timestamp, label, exit_code)
            content = table

        return Panel(
            content,
            title=f"[bold {self._color('surface_alt')}]{title}[/bold {self._color('surface_alt')}]",
            border_style=self._color("surface_alt"),
            box=box.ROUNDED,
            padding=(1, 1),
        )

    def _favorites_panel(self, favorites: List[Dict[str, Any]]) -> Panel:
        if not favorites:
            content = Text("No favorites yet. Favorite a command from its preview screen.", style=self._muted_style())
        else:
            table = Table(show_header=True, box=box.SIMPLE, header_style=f"bold {self._color('accent')}")
            table.add_column("Command", style=self._base_style())
            table.add_column("Saved", style=self._muted_style(), width=12)
            for entry in favorites:
                created_at = entry.get("created_at", "").split("T")[0]
                table.add_row(entry.get("label", "command"), created_at)
            content = table

        return Panel(
            content,
            title=f"[bold {self._color('accent')}]Favorites[/bold {self._color('accent')}]",
            border_style=self._color("accent"),
            box=box.ROUNDED,
            padding=(1, 1),
        )

    def _chip(self, label: str, value: str) -> Text:
        chip = Text()
        chip.append(f" {label} ", style=f"bold {self._color('text')} on {self._color('chip_bg')}")
        chip.append(" ")
        chip.append(str(value), style=f"bold {self._color('brand')}")
        return chip

    def _status_badge(self, text: str, token: str) -> str:
        color = self._color(token)
        return f"[bold {color}]{text}[/bold {color}]"

    def _format_bool(self, value: Optional[bool]) -> str:
        if value is True:
            return f"[{self._color('success')}]YES[/{self._color('success')}]"
        if value is False:
            return f"[{self._color('danger')}]NO[/{self._color('danger')}]"
        return "[dim]UNKNOWN[/dim]"

    def _format_state(
        self, state_present: Optional[bool], state_resource_count: Optional[int]
    ) -> str:
        if state_present is True and state_resource_count is not None:
            return (
                f"[{self._color('success')}]AVAILABLE[/{self._color('success')}] "
                f"({state_resource_count} resources)"
            )
        if state_present is True:
            return f"[{self._color('success')}]AVAILABLE[/{self._color('success')}]"
        if state_present is False:
            return f"[{self._color('warning')}]NONE[/{self._color('warning')}]"
        return "[dim]UNKNOWN[/dim]"

    def _plain_state(
        self, state_present: Optional[bool], state_resource_count: Optional[int]
    ) -> str:
        if state_present is True and state_resource_count is not None:
            return f"{state_resource_count} resources"
        if state_present is True:
            return "Available"
        if state_present is False:
            return "No state"
        return "Unknown"

    def _plain_guardrail(self, snapshot: Dict[str, Any]) -> str:
        parts = []
        parts.append("init" if snapshot.get("initialized") else "not init")
        parts.append("backend" if snapshot.get("backend_configured") else "local state")
        parts.append("locked" if snapshot.get("lock_file_present") else "no lock")
        return " / ".join(parts)

    def _base_style(self) -> str:
        return self._color("text")

    def _muted_style(self) -> str:
        return self._color("muted")

    def _color(self, token: str) -> str:
        return self.palette.get(token, "white")

    def _logo_width(self) -> int:
        if self.console.size.width >= 130:
            return 22
        if self.console.size.width >= 110:
            return 18
        if self.console.size.width >= 90:
            return 14
        return 10
