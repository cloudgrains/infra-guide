"""Tests for DriftDetector."""

import json
from infra_guide.drift_detector import DriftDetector


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _patch(monkeypatch, returncode=0, stdout="", stderr=""):
    monkeypatch.setattr(
        "infra_guide.drift_detector.subprocess.run",
        lambda *a, **kw: _Proc(returncode, stdout, stderr),
    )


def _drift_line(addr="aws_instance.web", action="update"):
    return json.dumps({"type": "resource_drift", "change": {"resource": {"addr": addr}, "action": action}})


# ── detect_drift ──────────────────────────────────────────────────────────────


def test_detect_drift_no_drift(monkeypatch):
    _patch(monkeypatch, returncode=0, stdout='{"type": "planned_change"}\n')
    detector = DriftDetector("tofu")
    result = detector.detect_drift()
    assert result["success"] is True
    assert result["drift_detected"] is False
    assert result["drift_count"] == 0


def test_detect_drift_with_drift(monkeypatch):
    line = _drift_line()
    _patch(monkeypatch, returncode=0, stdout=line + "\n")
    detector = DriftDetector("tofu")
    result = detector.detect_drift()
    assert result["success"] is True
    assert result["drift_detected"] is True
    assert result["drift_count"] == 1


def test_detect_drift_multiple_drifted_resources(monkeypatch):
    output = "\n".join([_drift_line("aws_vpc.main"), _drift_line("aws_instance.web")]) + "\n"
    _patch(monkeypatch, returncode=0, stdout=output)
    detector = DriftDetector("tofu")
    result = detector.detect_drift()
    assert result["drift_count"] == 2


def test_detect_drift_returns_failure_on_nonzero_exit(monkeypatch):
    _patch(monkeypatch, returncode=1, stderr="not initialized")
    detector = DriftDetector("tofu")
    result = detector.detect_drift()
    assert result["success"] is False
    assert "error" in result


def test_detect_drift_handles_malformed_json_lines(monkeypatch):
    output = "not-json\n" + _drift_line() + "\n"
    _patch(monkeypatch, returncode=0, stdout=output)
    detector = DriftDetector("tofu")
    result = detector.detect_drift()
    assert result["success"] is True
    assert result["drift_count"] == 1


def test_detect_drift_timeout(monkeypatch):
    import subprocess as _subprocess

    def _raise(*a, **kw):
        raise _subprocess.TimeoutExpired(cmd="tofu plan", timeout=300)

    monkeypatch.setattr("infra_guide.drift_detector.subprocess.run", _raise)
    detector = DriftDetector("tofu")
    result = detector.detect_drift()
    assert result["success"] is False
    assert "timed out" in result["error"].lower()


def test_detect_drift_exception(monkeypatch):
    def _raise(*a, **kw):
        raise OSError("binary not found")

    monkeypatch.setattr("infra_guide.drift_detector.subprocess.run", _raise)
    detector = DriftDetector("tofu")
    result = detector.detect_drift()
    assert result["success"] is False
    assert "failed" in result["error"].lower()
