"""Tests for UpdateChecker."""

import json
from infra_guide.update_checker import UpdateChecker, _version_is_newer


# ── _version_is_newer ─────────────────────────────────────────────────────────


def test_newer_version_detected():
    assert _version_is_newer("1.0.0", "0.8.0") is True


def test_same_version_not_newer():
    assert _version_is_newer("0.8.0", "0.8.0") is False


def test_older_version_not_newer():
    assert _version_is_newer("0.7.0", "0.8.0") is False


def test_version_comparison_with_patch():
    assert _version_is_newer("0.8.1", "0.8.0") is True


# ── UpdateChecker.get_notification ───────────────────────────────────────────


def test_notification_shown_when_newer_version_available():
    checker = UpdateChecker("0.8.0")
    checker._result = "1.0.0"
    checker._done.set()

    notification = checker.get_notification()
    assert notification is not None
    assert "1.0.0" in notification
    assert "upgrade" in notification.lower() or "update" in notification.lower()


def test_no_notification_when_up_to_date():
    checker = UpdateChecker("0.8.0")
    checker._result = "0.8.0"
    checker._done.set()

    assert checker.get_notification() is None


def test_no_notification_when_check_fails():
    checker = UpdateChecker("0.8.0")
    checker._result = None
    checker._done.set()

    assert checker.get_notification() is None


def test_no_notification_when_not_yet_complete():
    checker = UpdateChecker("0.8.0")
    # _done is not set → background thread still "running"
    assert checker.get_notification(timeout=0.01) is None


# ── UpdateChecker.start with cached result ────────────────────────────────────


def test_start_uses_cache_when_valid(tmp_path, monkeypatch):
    cache_file = tmp_path / "latest_version.json"
    import time

    cache_file.write_text(json.dumps({"version": "0.8.0", "ts": time.time()}))

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setattr(
        "infra_guide.update_checker._cache_path",
        lambda: str(cache_file),
    )

    checker = UpdateChecker("0.7.0")
    checker.start()
    assert checker._result == "0.8.0"
    assert checker._done.is_set()
