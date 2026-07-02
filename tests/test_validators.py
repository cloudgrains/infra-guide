"""Tests for PreFlightValidator."""

from infra_guide.validators import PreFlightValidator


# ── helpers ──────────────────────────────────────────────────────────────────


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _patch_run(monkeypatch, returncode=0, stdout="", stderr=""):
    monkeypatch.setattr(
        "infra_guide.validators.subprocess.run",
        lambda *a, **kw: _Proc(returncode, stdout, stderr),
    )


# ── configuration files ───────────────────────────────────────────────────────


def test_check_configuration_files_pass(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    v = PreFlightValidator("tofu")
    result = v._check_configuration_files()
    assert result["status"] == "pass"
    assert ".tf" in result["message"]


def test_check_configuration_files_fail(tmp_empty_workspace, monkeypatch):
    monkeypatch.chdir(tmp_empty_workspace)
    v = PreFlightValidator("tofu")
    result = v._check_configuration_files()
    assert result["status"] == "fail"


# ── initialization ────────────────────────────────────────────────────────────


def test_check_initialization_pass(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    v = PreFlightValidator("tofu")
    result = v._check_initialization()
    assert result["status"] == "pass"


def test_check_initialization_warning_when_no_dot_terraform(tmp_empty_workspace, monkeypatch):
    monkeypatch.chdir(tmp_empty_workspace)
    v = PreFlightValidator("tofu")
    result = v._check_initialization()
    assert result["status"] == "warning"


# ── syntax validation ─────────────────────────────────────────────────────────


def test_check_syntax_pass(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    _patch_run(monkeypatch, returncode=0)
    v = PreFlightValidator("tofu")
    result = v._check_syntax()
    assert result["status"] == "pass"


def test_check_syntax_fail(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    _patch_run(monkeypatch, returncode=1, stderr="error in main.tf")
    v = PreFlightValidator("tofu")
    result = v._check_syntax()
    assert result["status"] == "fail"


def test_check_syntax_skipped_when_no_tf_files(tmp_empty_workspace, monkeypatch):
    monkeypatch.chdir(tmp_empty_workspace)
    v = PreFlightValidator("tofu")
    result = v._check_syntax()
    assert result["status"] == "warning"
    assert "Skipped" in result["message"]


# ── formatting ────────────────────────────────────────────────────────────────


def test_check_formatting_pass(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    _patch_run(monkeypatch, returncode=0)
    v = PreFlightValidator("tofu")
    result = v._check_formatting()
    assert result["status"] == "pass"


def test_check_formatting_warning_when_unformatted(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    _patch_run(monkeypatch, returncode=1)
    v = PreFlightValidator("tofu")
    result = v._check_formatting()
    assert result["status"] == "warning"


# ── backend config ────────────────────────────────────────────────────────────


def test_check_backend_config_detected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "backend.tf").write_text('backend "s3" {}\n')
    v = PreFlightValidator("tofu")
    result = v._check_backend_config()
    assert result["status"] == "pass"


def test_check_backend_config_missing(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    v = PreFlightValidator("tofu")
    result = v._check_backend_config()
    assert result["status"] == "warning"


# ── provider versions ─────────────────────────────────────────────────────────


def test_check_provider_versions_pass(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    v = PreFlightValidator("tofu")
    result = v._check_provider_versions()
    assert result["status"] == "pass"


def test_check_provider_versions_warning_without_lock(tmp_empty_workspace, monkeypatch):
    monkeypatch.chdir(tmp_empty_workspace)
    (tmp_empty_workspace / "main.tf").write_text("# tf\n")
    v = PreFlightValidator("tofu")
    result = v._check_provider_versions()
    assert result["status"] == "warning"


# ── run_all_checks ────────────────────────────────────────────────────────────


def test_run_all_checks_returns_counts(tmp_workspace, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    _patch_run(monkeypatch, returncode=0)
    v = PreFlightValidator("tofu")
    results = v.run_all_checks()
    assert results["total"] == 7
    assert results["passed"] + results["warnings"] + results["failed"] == 7
