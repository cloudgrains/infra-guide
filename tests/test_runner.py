"""Tests for CommandRunner."""

from infra_guide.runner import CommandRunner


# ── build_command ─────────────────────────────────────────────────────────────


def test_build_command_basic():
    runner = CommandRunner("tofu")
    assert runner.build_command("init") == ["tofu", "init"]


def test_build_command_with_additional_args():
    runner = CommandRunner("terraform")
    cmd = runner.build_command("plan", ["-out=plan.out", "-var=env=prod"])
    assert cmd == ["terraform", "plan", "-out=plan.out", "-var=env=prod"]


def test_build_command_none_args_ignored():
    runner = CommandRunner("tofu")
    assert runner.build_command("apply", None) == ["tofu", "apply"]


def test_build_command_empty_args_ignored():
    runner = CommandRunner("tofu")
    assert runner.build_command("destroy", []) == ["tofu", "destroy"]


def test_build_command_uses_tool_name():
    runner = CommandRunner("terraform")
    cmd = runner.build_command("init")
    assert cmd[0] == "terraform"


# ── format_command ────────────────────────────────────────────────────────────


def test_format_command_returns_string():
    runner = CommandRunner("tofu")
    result = runner.format_command("init")
    assert isinstance(result, str)
    assert "tofu" in result
    assert "init" in result


def test_format_command_quotes_args_with_spaces():
    runner = CommandRunner("tofu")
    result = runner.format_command("plan", ["-var=name=my app"])
    assert "my app" in result or '"my app"' in result or "'my app'" in result


# ── execute_capture ───────────────────────────────────────────────────────────


class _FakeProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_execute_capture_success(monkeypatch):
    monkeypatch.setattr(
        "infra_guide.runner.subprocess.run",
        lambda *a, **kw: _FakeProc(0, "Initialized successfully.\n"),
    )
    runner = CommandRunner("tofu")
    result = runner.execute_capture("init")
    assert result["success"] is True
    assert result["exit_code"] == 0
    assert "Initialized" in result["stdout"]
    assert "command" in result
    assert "duration_seconds" in result


def test_execute_capture_failure(monkeypatch):
    monkeypatch.setattr(
        "infra_guide.runner.subprocess.run",
        lambda *a, **kw: _FakeProc(1, "", "Error: no config files"),
    )
    runner = CommandRunner("tofu")
    result = runner.execute_capture("plan")
    assert result["success"] is False
    assert result["exit_code"] == 1
    assert "Error" in result["stderr"]


def test_execute_capture_exception(monkeypatch):
    def _raise(*a, **kw):
        raise OSError("binary not found")

    monkeypatch.setattr("infra_guide.runner.subprocess.run", _raise)
    runner = CommandRunner("tofu")
    result = runner.execute_capture("init")
    assert result["success"] is False
    assert result["exit_code"] == 1
    assert "binary not found" in result["stderr"]


def test_execute_capture_includes_command_preview(monkeypatch):
    monkeypatch.setattr(
        "infra_guide.runner.subprocess.run",
        lambda *a, **kw: _FakeProc(0, ""),
    )
    runner = CommandRunner("tofu")
    result = runner.execute_capture("fmt", ["-check"])
    assert "tofu" in result["command"]
    assert "fmt" in result["command"]


# ── execute_with_flags ────────────────────────────────────────────────────────


def test_execute_with_flags_boolean_true(monkeypatch):
    captured = {}

    def _fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return _FakeProc(0)

    monkeypatch.setattr("infra_guide.runner.subprocess.run", _fake_run)
    runner = CommandRunner("tofu")
    runner.execute_with_flags("init", {"-upgrade": True})
    assert "-upgrade" in captured["cmd"]


def test_execute_with_flags_value_flag(monkeypatch):
    captured = {}

    def _fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return _FakeProc(0)

    monkeypatch.setattr("infra_guide.runner.subprocess.run", _fake_run)
    runner = CommandRunner("tofu")
    runner.execute_with_flags("plan", {"-out": "myplan"})
    assert "-out" in captured["cmd"]
    assert "myplan" in captured["cmd"]


def test_execute_with_flags_false_flag_skipped(monkeypatch):
    captured = {}

    def _fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return _FakeProc(0)

    monkeypatch.setattr("infra_guide.runner.subprocess.run", _fake_run)
    runner = CommandRunner("tofu")
    runner.execute_with_flags("fmt", {"-check": False})
    assert "-check" not in captured["cmd"]
