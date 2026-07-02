"""Tests for WorkspaceManager."""

from infra_guide.workspace_manager import WorkspaceManager


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _patch(monkeypatch, returncode=0, stdout="", stderr=""):
    monkeypatch.setattr(
        "infra_guide.workspace_manager.subprocess.run",
        lambda *a, **kw: _Proc(returncode, stdout, stderr),
    )


# ── list_workspaces ───────────────────────────────────────────────────────────


def test_list_workspaces_parses_current(monkeypatch):
    _patch(monkeypatch, stdout="  default\n* staging\n  prod\n")
    wm = WorkspaceManager("tofu")
    result = wm.list_workspaces()
    assert result["success"] is True
    assert result["current"] == "staging"
    assert "staging" in result["workspaces"]
    assert "default" in result["workspaces"]
    assert "prod" in result["workspaces"]
    assert result["count"] == 3


def test_list_workspaces_failure(monkeypatch):
    _patch(monkeypatch, returncode=1, stderr="backend not initialized")
    wm = WorkspaceManager("tofu")
    result = wm.list_workspaces()
    assert result["success"] is False
    assert "error" in result


def test_list_workspaces_default_when_no_star(monkeypatch):
    _patch(monkeypatch, stdout="  default\n")
    wm = WorkspaceManager("tofu")
    result = wm.list_workspaces()
    assert result["current"] == "default"


# ── create_workspace ──────────────────────────────────────────────────────────


def test_create_workspace_success(monkeypatch):
    _patch(monkeypatch, returncode=0)
    wm = WorkspaceManager("tofu")
    result = wm.create_workspace("feature-x")
    assert result["success"] is True


def test_create_workspace_failure(monkeypatch):
    _patch(monkeypatch, returncode=1, stderr="already exists")
    wm = WorkspaceManager("tofu")
    result = wm.create_workspace("duplicate")
    assert result["success"] is False


# ── select_workspace ──────────────────────────────────────────────────────────


def test_select_workspace_success(monkeypatch):
    _patch(monkeypatch, returncode=0)
    wm = WorkspaceManager("tofu")
    result = wm.select_workspace("prod")
    assert result["success"] is True


# ── delete_workspace ──────────────────────────────────────────────────────────


def test_delete_workspace_success(monkeypatch):
    _patch(monkeypatch, returncode=0)
    wm = WorkspaceManager("tofu")
    result = wm.delete_workspace("old-workspace")
    assert result["success"] is True


# ── exception handling ────────────────────────────────────────────────────────


def test_list_workspaces_exception_returns_failure(monkeypatch):
    def _raise(*a, **kw):
        raise OSError("connection refused")

    monkeypatch.setattr("infra_guide.workspace_manager.subprocess.run", _raise)
    wm = WorkspaceManager("tofu")
    result = wm.list_workspaces()
    assert result["success"] is False
