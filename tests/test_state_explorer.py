"""Tests for StateExplorer."""

import json
import pytest
from infra_guide.state_explorer import StateExplorer


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


# ── list_resources ────────────────────────────────────────────────────────────


def test_list_resources_simple_address(monkeypatch):
    """aws_vpc.main → type should be aws_vpc (second-to-last segment)."""
    monkeypatch.setattr(
        "infra_guide.state_explorer.subprocess.run",
        lambda *a, **kw: _Proc(0, "aws_vpc.main\n"),
    )
    explorer = StateExplorer("tofu")
    resources = explorer.list_resources()
    assert len(resources) == 1
    assert resources[0]["address"] == "aws_vpc.main"
    assert resources[0]["type"] == "aws_vpc"


def test_list_resources_module_address(monkeypatch):
    """module.network.aws_vpc.main → type should be aws_vpc (the bug fix)."""
    monkeypatch.setattr(
        "infra_guide.state_explorer.subprocess.run",
        lambda *a, **kw: _Proc(0, "module.network.aws_vpc.main\n"),
    )
    explorer = StateExplorer("tofu")
    resources = explorer.list_resources()
    assert resources[0]["type"] == "aws_vpc"


def test_list_resources_deeply_nested_module(monkeypatch):
    """module.a.module.b.aws_s3_bucket.assets → type should be aws_s3_bucket."""
    monkeypatch.setattr(
        "infra_guide.state_explorer.subprocess.run",
        lambda *a, **kw: _Proc(0, "module.a.module.b.aws_s3_bucket.assets\n"),
    )
    explorer = StateExplorer("tofu")
    resources = explorer.list_resources()
    assert resources[0]["type"] == "aws_s3_bucket"


def test_list_resources_empty_state(monkeypatch):
    monkeypatch.setattr(
        "infra_guide.state_explorer.subprocess.run",
        lambda *a, **kw: _Proc(0, ""),
    )
    explorer = StateExplorer("tofu")
    resources = explorer.list_resources()
    assert resources == []


def test_list_resources_returns_empty_on_failure(monkeypatch):
    monkeypatch.setattr(
        "infra_guide.state_explorer.subprocess.run",
        lambda *a, **kw: _Proc(1, "", "No state file"),
    )
    explorer = StateExplorer("tofu")
    assert explorer.list_resources() == []


def test_list_resources_returns_empty_on_exception(monkeypatch):
    def _raise(*a, **kw):
        raise OSError("not found")

    monkeypatch.setattr("infra_guide.state_explorer.subprocess.run", _raise)
    explorer = StateExplorer("tofu")
    assert explorer.list_resources() == []


def test_list_resources_multiple(monkeypatch):
    output = "aws_vpc.main\naws_subnet.private\naws_security_group.web\n"
    monkeypatch.setattr(
        "infra_guide.state_explorer.subprocess.run",
        lambda *a, **kw: _Proc(0, output),
    )
    explorer = StateExplorer("tofu")
    resources = explorer.list_resources()
    assert len(resources) == 3
    types = {r["type"] for r in resources}
    assert types == {"aws_vpc", "aws_subnet", "aws_security_group"}


# ── get_state_data ────────────────────────────────────────────────────────────


def test_get_state_data_success(monkeypatch):
    state = {"terraform_version": "1.7.0", "values": {}}
    monkeypatch.setattr(
        "infra_guide.state_explorer.subprocess.run",
        lambda *a, **kw: _Proc(0, json.dumps(state)),
    )
    explorer = StateExplorer("tofu")
    data = explorer.get_state_data()
    assert data is not None
    assert data["terraform_version"] == "1.7.0"


def test_get_state_data_returns_none_on_failure(monkeypatch):
    monkeypatch.setattr(
        "infra_guide.state_explorer.subprocess.run",
        lambda *a, **kw: _Proc(1, "", "No state"),
    )
    explorer = StateExplorer("tofu")
    assert explorer.get_state_data() is None


# ── get_state_stats ───────────────────────────────────────────────────────────


def test_get_state_stats_structure(monkeypatch):
    """Stats dict must always include total_resources, resource_types, has_state."""
    monkeypatch.setattr(
        "infra_guide.state_explorer.subprocess.run",
        lambda *a, **kw: _Proc(1, "", "no state"),
    )
    explorer = StateExplorer("tofu")
    stats = explorer.get_state_stats()
    assert "total_resources" in stats
    assert "resource_types" in stats
    assert "has_state" in stats


def test_get_state_stats_counts_resources(monkeypatch):
    output = "aws_vpc.main\naws_vpc.secondary\naws_subnet.private\n"

    def _fake_run(cmd, *a, **kw):
        if "show" in cmd:
            return _Proc(1)  # no JSON state
        return _Proc(0, output)

    monkeypatch.setattr("infra_guide.state_explorer.subprocess.run", _fake_run)
    explorer = StateExplorer("tofu")
    stats = explorer.get_state_stats()
    assert stats["total_resources"] == 3
    assert stats["resource_types"] == 2  # aws_vpc and aws_subnet
