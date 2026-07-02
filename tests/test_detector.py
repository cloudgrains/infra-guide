"""Tests for ToolDetector."""

import pytest
from infra_guide.detector import ToolDetector


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_detect_prefers_tofu_when_both_present(monkeypatch):
    monkeypatch.setattr("infra_guide.detector.shutil.which", lambda name: "/usr/bin/" + name)
    assert ToolDetector.detect() == "tofu"


def test_detect_falls_back_to_terraform(monkeypatch):
    monkeypatch.setattr(
        "infra_guide.detector.shutil.which",
        lambda name: None if name == "tofu" else "/usr/bin/terraform",
    )
    assert ToolDetector.detect() == "terraform"


def test_detect_returns_none_when_nothing_installed(monkeypatch):
    monkeypatch.setattr("infra_guide.detector.shutil.which", lambda name: None)
    assert ToolDetector.detect() is None


def test_get_version_returns_first_line(monkeypatch):
    import subprocess as _subprocess

    monkeypatch.setattr(
        _subprocess,
        "run",
        lambda *a, **kw: _Proc(0, "OpenTofu v1.7.0\nsome extra\n"),
    )
    assert ToolDetector.get_version("tofu") == "OpenTofu v1.7.0"


def test_get_version_returns_unknown_on_failure(monkeypatch):
    import subprocess as _subprocess

    monkeypatch.setattr(
        _subprocess,
        "run",
        lambda *a, **kw: _Proc(1, "", "error"),
    )
    assert ToolDetector.get_version("tofu") == "unknown"


def test_get_version_returns_unknown_on_exception(monkeypatch):
    import subprocess as _subprocess

    def _raise(*a, **kw):
        raise OSError("not found")

    monkeypatch.setattr(_subprocess, "run", _raise)
    assert ToolDetector.get_version("tofu") == "unknown"
