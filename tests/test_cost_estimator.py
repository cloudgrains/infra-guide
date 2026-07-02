from infra_guide.cost_estimator import CostEstimator


def test_estimate_apply_cost_without_plan_and_without_aws_returns_unavailable(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    estimator = CostEstimator("tofu")
    result = estimator.estimate_apply_cost([])

    assert result["exact_estimate_available"] is False
    assert result["impact"] == "unknown"
    assert "No saved plan file" in result["summary"]


def test_estimate_apply_cost_from_aws_plan_returns_warning(monkeypatch):
    estimator = CostEstimator("tofu")

    monkeypatch.setattr(
        estimator,
        "_load_plan_json",
        lambda path: {
            "resource_changes": [
                {
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "type": "aws_instance",
                    "change": {"actions": ["create"]},
                },
                {
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "type": "aws_s3_bucket",
                    "change": {"actions": ["update"]},
                },
            ]
        },
    )

    monkeypatch.setattr(
        estimator,
        "_extract_plan_file",
        lambda args: "tfplan",
    )

    result = estimator.estimate_apply_cost(["tfplan"])

    assert result["status"] == "warning"
    assert result["impact"] == "high"
    assert result["exact_estimate_available"] is False


def test_estimate_apply_cost_low_impact_resources(monkeypatch):
    estimator = CostEstimator("tofu")

    monkeypatch.setattr(
        estimator,
        "_load_plan_json",
        lambda path: {
            "resource_changes": [
                {
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "type": "aws_iam_role",
                    "change": {"actions": ["create"]},
                },
            ]
        },
    )
    monkeypatch.setattr(estimator, "_extract_plan_file", lambda args: "tfplan")
    result = estimator.estimate_apply_cost(["tfplan"])
    assert result["impact"] in ("low", "medium", "unknown")


def test_estimate_apply_cost_no_resources(monkeypatch):
    estimator = CostEstimator("tofu")

    monkeypatch.setattr(
        estimator,
        "_load_plan_json",
        lambda path: {"resource_changes": []},
    )
    monkeypatch.setattr(estimator, "_extract_plan_file", lambda args: "tfplan")
    result = estimator.estimate_apply_cost(["tfplan"])
    assert result["exact_estimate_available"] is False
