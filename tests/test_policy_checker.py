"""Tests for PolicyChecker."""

import json
import pytest
from infra_guide.policy_checker import PolicyChecker


def _plan_json(resource_changes):
    return json.dumps({"resource_changes": resource_changes})


def _change(resource_type, name, after_values, action="create"):
    return {
        "type": resource_type,
        "name": name,
        "change": {"actions": [action], "after": after_values},
        "provider_name": "registry.terraform.io/hashicorp/aws",
    }


# ── basic wiring ──────────────────────────────────────────────────────────────


def test_check_plan_returns_success_structure():
    checker = PolicyChecker()
    result = checker.check_plan(_plan_json([]))
    assert result["success"] is True
    assert result["total_checks"] == 0
    assert result["violations"] == 0


def test_check_plan_invalid_json_returns_failure():
    checker = PolicyChecker()
    result = checker.check_plan("not-json")
    assert result["success"] is False
    assert "error" in result


# ── no-public-s3 policy ───────────────────────────────────────────────────────


def test_public_s3_bucket_triggers_violation():
    checker = PolicyChecker()
    plan = _plan_json([_change("aws_s3_bucket", "assets", {"acl": "public-read"})])
    result = checker.check_plan(plan)
    ids = [v["policy_id"] for v in result["violation_details"]]
    assert "no-public-s3" in ids


def test_private_s3_bucket_passes_no_public_s3_policy():
    checker = PolicyChecker()
    plan = _plan_json([_change("aws_s3_bucket", "logs", {"acl": "private"})])
    result = checker.check_plan(plan)
    ids = [v["policy_id"] for v in result["violation_details"]]
    assert "no-public-s3" not in ids


# ── no-public-ingress policy ──────────────────────────────────────────────────


def test_open_security_group_triggers_violation():
    checker = PolicyChecker()
    plan = _plan_json(
        [
            _change(
                "aws_security_group",
                "wide_open",
                {"ingress": [{"cidr_blocks": ["0.0.0.0/0"], "from_port": 0}]},
            )
        ]
    )
    result = checker.check_plan(plan)
    ids = [v["policy_id"] for v in result["violation_details"]]
    assert "no-public-ingress" in ids


def test_restricted_security_group_passes():
    checker = PolicyChecker()
    plan = _plan_json(
        [
            _change(
                "aws_security_group",
                "office_only",
                {"ingress": [{"cidr_blocks": ["10.0.0.0/8"], "from_port": 443}]},
            )
        ]
    )
    result = checker.check_plan(plan)
    ids = [v["policy_id"] for v in result["violation_details"]]
    assert "no-public-ingress" not in ids


# ── require-tags policy ───────────────────────────────────────────────────────


def test_resource_without_required_tags_triggers_violation():
    checker = PolicyChecker()
    plan = _plan_json([_change("aws_instance", "web", {"tags": {}})])
    result = checker.check_plan(plan)
    ids = [v["policy_id"] for v in result["violation_details"]]
    assert "require-tags" in ids


def test_resource_with_required_tags_passes():
    checker = PolicyChecker()
    plan = _plan_json(
        [
            _change(
                "aws_instance",
                "web",
                {"tags": {"Environment": "prod", "Owner": "platform"}},
            )
        ]
    )
    result = checker.check_plan(plan)
    ids = [v["policy_id"] for v in result["violation_details"]]
    assert "require-tags" not in ids


# ── update actions are also checked ──────────────────────────────────────────


def test_update_actions_are_checked():
    checker = PolicyChecker()
    plan = _plan_json(
        [_change("aws_s3_bucket", "logs", {"acl": "public-read-write"}, action="update")]
    )
    result = checker.check_plan(plan)
    ids = [v["policy_id"] for v in result["violation_details"]]
    assert "no-public-s3" in ids


# ── delete actions are skipped ────────────────────────────────────────────────


def test_delete_actions_are_not_checked():
    checker = PolicyChecker()
    plan = _plan_json(
        [_change("aws_s3_bucket", "old", {"acl": "public-read"}, action="delete")]
    )
    result = checker.check_plan(plan)
    assert result["total_checks"] == 0


# ── violation severity ────────────────────────────────────────────────────────


def test_open_sg_violation_is_critical():
    checker = PolicyChecker()
    plan = _plan_json(
        [
            _change(
                "aws_security_group",
                "wide",
                {"ingress": [{"cidr_blocks": ["0.0.0.0/0"]}]},
            )
        ]
    )
    result = checker.check_plan(plan)
    sg_violations = [v for v in result["violation_details"] if v["policy_id"] == "no-public-ingress"]
    assert sg_violations[0]["severity"] == "critical"
