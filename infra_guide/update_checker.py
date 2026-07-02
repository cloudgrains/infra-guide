"""
Background PyPI version checker with XDG-compliant cache.

Starts a daemon thread on first call; the caller polls `get_result()` after
its main work completes so the network round-trip doesn't block UX.
"""

import json
import os
import threading
import time
from typing import Optional, Tuple

_PACKAGE = "infra-guide"
_PYPI_URL = "https://pypi.org/pypi/infra-guide/json"
_CACHE_TTL = 86400  # 24 hours


def _cache_path() -> str:
    base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    directory = os.path.join(base, "infra-guide")
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, "latest_version.json")


def _read_cache() -> Optional[Tuple[str, float]]:
    """Return (version, timestamp) from cache, or None if missing/expired."""
    try:
        with open(_cache_path(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if time.time() - data["ts"] < _CACHE_TTL:
            return data["version"], data["ts"]
    except Exception:
        pass
    return None


def _write_cache(version: str) -> None:
    try:
        with open(_cache_path(), "w", encoding="utf-8") as fh:
            json.dump({"version": version, "ts": time.time()}, fh)
    except Exception:
        pass


def _fetch_latest() -> Optional[str]:
    """Fetch latest version from PyPI. Returns version string or None."""
    try:
        import urllib.request

        with urllib.request.urlopen(_PYPI_URL, timeout=5) as resp:  # noqa: S310
            data = json.loads(resp.read())
            return data["info"]["version"]
    except Exception:
        return None


class UpdateChecker:
    """
    Non-blocking update checker.

    Usage:
        checker = UpdateChecker(current_version)
        checker.start()
        # ... do the main CLI work ...
        notification = checker.get_notification()
        if notification:
            console.print(notification)
    """

    def __init__(self, current_version: str):
        self._current = current_version
        self._result: Optional[str] = None
        self._done = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Kick off the background version check."""
        cached = _read_cache()
        if cached:
            self._result = cached[0]
            self._done.set()
            return

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        version = _fetch_latest()
        if version:
            _write_cache(version)
            self._result = version
        self._done.set()

    def get_notification(self, timeout: float = 0.1) -> Optional[str]:
        """
        Wait up to `timeout` seconds for the check to finish.

        Returns a Rich-formatted notification string if an update is available,
        or None otherwise.
        """
        self._done.wait(timeout)
        latest = self._result
        if not latest:
            return None
        if _version_is_newer(latest, self._current):
            return (
                f"\n[bold yellow]  A new version of infra-guide is available![/bold yellow]\n"
                f"  Current: [dim]{self._current}[/dim]  →  "
                f"Latest: [bold green]{latest}[/bold green]\n"
                f"  Run [cyan]pip install --upgrade infra-guide[/cyan] to update.\n"
            )
        return None


def _version_is_newer(latest: str, current: str) -> bool:
    """Return True if latest is strictly greater than current."""
    try:
        from packaging.version import Version

        return Version(latest) > Version(current)
    except Exception:
        return latest != current
