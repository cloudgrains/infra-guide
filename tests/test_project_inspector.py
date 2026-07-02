"""Tests for ProjectInspector."""

import pytest
from infra_guide.project_inspector import ProjectInspector


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _patch_workspace(monkeypatch, workspace="default"):
    monkeypatch.setattr(
        "infra_guide.project_inspector.subprocess.run",
        lambda *a, **kw: _Proc(0, workspace + "\n"),
    )


def test_inspect_empty_workspace(tmp_empty_workspace, monkeypatch):
    monkeypatch.chdir(tmp_empty_workspace)
    _patch_workspace(monkeypatch)
    inspector = ProjectInspector("tofu")
    snap = inspector.inspect(include_state=False)
    assert snap["tf_file_count"] == 0
    assert snap["readiness"] == "empty"


def test_inspect_initialized_workspace(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    _patch_workspace(monkeypatch)
    inspector = ProjectInspector("tofu")
    snap = inspector.inspect(include_state=False)
    assert snap["tf_file_count"] == 1
    assert snap["initialized"] is True
    assert snap["lock_file_present"] is True


def test_inspect_readiness_needs_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _patch_workspace(monkeypatch)
    (tmp_path / "main.tf").write_text("# tf\n")
    inspector = ProjectInspector("tofu")
    snap = inspector.inspect(include_state=False)
    assert snap["readiness"] == "needs_init"
    assert "init" in snap["recommendation"].lower()


def test_inspect_counts_module_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _patch_workspace(monkeypatch)
    (tmp_path / ".terraform").mkdir()
    (tmp_path / "main.tf").write_text(
        'module "vpc" {}\nmodule "app" {}\nprovider "aws" {}\n'
    )
    inspector = ProjectInspector("tofu")
    snap = inspector.inspect(include_state=False)
    assert snap["module_block_count"] == 2


def test_inspect_detects_backend(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _patch_workspace(monkeypatch)
    (tmp_path / ".terraform").mkdir()
    (tmp_path / "main.tf").write_text('backend "s3" {}\n')
    inspector = ProjectInspector("tofu")
    snap = inspector.inspect(include_state=False)
    assert snap["backend_configured"] is True


def test_inspect_workspace_fallback_on_error(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    monkeypatch.setattr(
        "infra_guide.project_inspector.subprocess.run",
        lambda *a, **kw: _Proc(1, "", "error"),
    )
    inspector = ProjectInspector("tofu")
    snap = inspector.inspect(include_state=False)
    assert snap["workspace"] == "unknown"


def test_guess_state_summary_detects_local_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _patch_workspace(monkeypatch)
    (tmp_path / "terraform.tfstate").write_text("{}")
    (tmp_path / "main.tf").write_text("# tf\n")
    (tmp_path / ".terraform").mkdir()
    inspector = ProjectInspector("tofu")
    snap = inspector.inspect(include_state=False)
    assert snap["state_present"] is True


def test_snapshot_as_dict_has_all_keys(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    _patch_workspace(monkeypatch)
    inspector = ProjectInspector("tofu")
    snap = inspector.inspect()
    required_keys = {
        "cwd", "tool_name", "workspace", "tf_file_count", "tfvars_file_count",
        "module_block_count", "initialized", "lock_file_present",
        "backend_configured", "state_present", "readiness", "readiness_label",
        "recommendation",
    }
    assert required_keys.issubset(snap.keys())
