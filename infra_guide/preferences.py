"""
Persistent user preferences for infra-guide.
"""

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


THEMES: Dict[str, Dict[str, str]] = {
    "aurora": {
        "label": "Aurora",
        "description": "Bright cyan and amber accents with a clean ops feel.",
        "brand": "bright_cyan",
        "accent": "cyan",
        "accent_alt": "bright_magenta",
        "surface": "blue",
        "surface_alt": "magenta",
        "text": "white",
        "muted": "grey70",
        "success": "green",
        "warning": "yellow",
        "danger": "bright_red",
        "info": "bright_cyan",
        "chip_bg": "grey23",
        "web_bg": "#06131d",
        "web_bg_alt": "#0a1826",
        "web_surface": "#102438",
        "web_surface_alt": "#15314a",
        "web_border": "#1e7db4",
        "web_text": "#f4fbff",
        "web_muted": "#8ea8b6",
        "web_brand": "#35d9ff",
        "web_accent": "#00c2ff",
        "web_accent_alt": "#ff61d2",
        "web_success": "#22c55e",
        "web_warning": "#f59e0b",
        "web_danger": "#ef4444",
        "web_chip_bg": "#163042",
    },
    "sunset": {
        "label": "Sunset",
        "description": "Warm amber and coral tones for a more vibrant terminal.",
        "brand": "bright_yellow",
        "accent": "yellow",
        "accent_alt": "bright_red",
        "surface": "dark_orange3",
        "surface_alt": "red",
        "text": "white",
        "muted": "grey74",
        "success": "green",
        "warning": "bright_yellow",
        "danger": "bright_red",
        "info": "bright_yellow",
        "chip_bg": "grey19",
        "web_bg": "#1a0f0a",
        "web_bg_alt": "#24140d",
        "web_surface": "#331c14",
        "web_surface_alt": "#472418",
        "web_border": "#a45d2f",
        "web_text": "#fff8f3",
        "web_muted": "#d3b8aa",
        "web_brand": "#ffbf47",
        "web_accent": "#ff9f43",
        "web_accent_alt": "#ff6f61",
        "web_success": "#34d399",
        "web_warning": "#fbbf24",
        "web_danger": "#f87171",
        "web_chip_bg": "#523122",
    },
    "forest": {
        "label": "Forest",
        "description": "Green-forward palette for a calmer terminal dashboard.",
        "brand": "green",
        "accent": "spring_green3",
        "accent_alt": "cyan",
        "surface": "green4",
        "surface_alt": "dark_sea_green4",
        "text": "white",
        "muted": "grey70",
        "success": "green",
        "warning": "yellow",
        "danger": "bright_red",
        "info": "cyan",
        "chip_bg": "grey19",
        "web_bg": "#081610",
        "web_bg_alt": "#0d1f17",
        "web_surface": "#132c20",
        "web_surface_alt": "#19402b",
        "web_border": "#2b7c4e",
        "web_text": "#f3fff8",
        "web_muted": "#a0b8ad",
        "web_brand": "#4ade80",
        "web_accent": "#22c55e",
        "web_accent_alt": "#2dd4bf",
        "web_success": "#4ade80",
        "web_warning": "#facc15",
        "web_danger": "#f87171",
        "web_chip_bg": "#1d3b2a",
    },
    "mono": {
        "label": "Mono",
        "description": "High-contrast neutral styling for minimal terminals.",
        "brand": "white",
        "accent": "grey93",
        "accent_alt": "grey70",
        "surface": "white",
        "surface_alt": "grey70",
        "text": "white",
        "muted": "grey62",
        "success": "white",
        "warning": "grey85",
        "danger": "grey93",
        "info": "grey85",
        "chip_bg": "grey19",
        "web_bg": "#0d0d0d",
        "web_bg_alt": "#121212",
        "web_surface": "#1b1b1b",
        "web_surface_alt": "#252525",
        "web_border": "#5f5f5f",
        "web_text": "#f5f5f5",
        "web_muted": "#b2b2b2",
        "web_brand": "#ffffff",
        "web_accent": "#e5e5e5",
        "web_accent_alt": "#bdbdbd",
        "web_success": "#fafafa",
        "web_warning": "#d4d4d4",
        "web_danger": "#ffffff",
        "web_chip_bg": "#2d2d2d",
    },
}

DEFAULT_THEME = "aurora"
DEFAULT_DATA = {
    "theme": DEFAULT_THEME,
    "favorites": [],
    "history": [],
}
MAX_HISTORY = 40


def get_theme_palette(theme_name: Optional[str]) -> Dict[str, str]:
    """Return a validated theme palette."""
    if theme_name in THEMES:
        return THEMES[theme_name]
    return THEMES[DEFAULT_THEME]


def get_web_theme_palette(theme_name: Optional[str]) -> Dict[str, str]:
    """Return CSS-friendly colors for the requested theme."""
    palette = get_theme_palette(theme_name)
    return {
        "bg": palette["web_bg"],
        "bg_alt": palette["web_bg_alt"],
        "surface": palette["web_surface"],
        "surface_alt": palette["web_surface_alt"],
        "border": palette["web_border"],
        "text": palette["web_text"],
        "muted": palette["web_muted"],
        "brand": palette["web_brand"],
        "accent": palette["web_accent"],
        "accent_alt": palette["web_accent_alt"],
        "success": palette["web_success"],
        "warning": palette["web_warning"],
        "danger": palette["web_danger"],
        "chip_bg": palette["web_chip_bg"],
    }


class PreferencesStore:
    """Manage user preferences and recent command history."""

    def __init__(self):
        self.path = self._resolve_path()
        self._data = self._load()

    def get_theme_name(self) -> str:
        """Return the persisted theme name."""
        theme_name = self._data.get("theme", DEFAULT_THEME)
        if theme_name not in THEMES:
            return DEFAULT_THEME
        return theme_name

    def set_theme(self, theme_name: str) -> None:
        """Persist a theme selection."""
        if theme_name not in THEMES:
            raise ValueError(f"Unknown theme: {theme_name}")
        self._data["theme"] = theme_name
        self._save()

    def list_themes(self) -> Dict[str, Dict[str, str]]:
        """Return the full theme catalog."""
        return THEMES

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return recent history entries, newest first."""
        history = list(self._data.get("history", []))
        history.reverse()
        if limit is not None:
            return history[:limit]
        return history

    def clear_history(self) -> None:
        """Remove all history entries."""
        self._data["history"] = []
        self._save()

    def get_favorites(self) -> List[Dict[str, Any]]:
        """Return favorite command entries."""
        return list(self._data.get("favorites", []))

    def is_favorite(self, command_name: str, args: List[str]) -> bool:
        """Return True when a command is favorited."""
        key = self._make_key(command_name, args)
        return any(item.get("key") == key for item in self._data.get("favorites", []))

    def toggle_favorite(self, command_name: str, args: List[str], label: str) -> bool:
        """
        Toggle a favorite command.

        Returns:
            bool: True when the command is now favorited, False when removed.
        """
        key = self._make_key(command_name, args)
        favorites = list(self._data.get("favorites", []))

        for index, favorite in enumerate(favorites):
            if favorite.get("key") == key:
                favorites.pop(index)
                self._data["favorites"] = favorites
                self._save()
                return False

        favorites.append(
            {
                "key": key,
                "command_name": command_name,
                "args": list(args),
                "label": label,
                "created_at": self._timestamp(),
            }
        )
        self._data["favorites"] = favorites
        self._save()
        return True

    def remove_favorite(self, key: str) -> bool:
        """Remove a favorite by key."""
        favorites = list(self._data.get("favorites", []))
        new_favorites = [item for item in favorites if item.get("key") != key]
        if len(new_favorites) == len(favorites):
            return False
        self._data["favorites"] = new_favorites
        self._save()
        return True

    def record_execution(
        self,
        command_name: str,
        args: List[str],
        label: str,
        cwd: str,
        exit_code: int,
    ) -> None:
        """Append a command execution to history."""
        history = list(self._data.get("history", []))
        history.append(
            {
                "key": self._make_key(command_name, args),
                "command_name": command_name,
                "args": list(args),
                "label": label,
                "cwd": cwd,
                "exit_code": exit_code,
                "timestamp": self._timestamp(),
            }
        )
        self._data["history"] = history[-MAX_HISTORY:]
        self._save()

    def _resolve_path(self) -> Path:
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            base = Path(config_home)
        else:
            base = Path.home() / ".config"
        return base / "infra-guide" / "preferences.json"

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return dict(DEFAULT_DATA)

        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception:
            return dict(DEFAULT_DATA)

        data = dict(DEFAULT_DATA)
        if isinstance(payload, dict):
            data.update(payload)

        if data.get("theme") not in THEMES:
            data["theme"] = DEFAULT_THEME
        if not isinstance(data.get("favorites"), list):
            data["favorites"] = []
        if not isinstance(data.get("history"), list):
            data["history"] = []

        return data

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2)

    def _make_key(self, command_name: str, args: List[str]) -> str:
        return "|".join([command_name] + list(args))

    def _timestamp(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")
