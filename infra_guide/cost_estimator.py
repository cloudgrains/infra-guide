"""
Plan-aware cost insight helpers for apply workflows.
"""

import json
import os
import re
import subprocess
from collections import Counter
from typing import Any, Dict, List, Optional


AWS_PROVIDER_TOKEN = "aws"
HIGH_IMPACT_PREFIXES = (
    "aws_instance",
    "aws_db_",
    "aws_rds_",
    "aws_eks_",
    "aws_elasticache_",
    "aws_redshift_",
    "aws_opensearch_",
    "aws_nat_gateway",
    "aws_lb",
    "aws_autoscaling_",
    "aws_ecs_",
    "aws_msk_",
)
MEDIUM_IMPACT_PREFIXES = (
    "aws_s3_",
    "aws_ebs_",
    "aws_cloudfront_",
    "aws_eip",
    "aws_backup_",
    "aws_vpn_",
    "aws_dx_",
)
AWS_CONFIG_PATTERN = re.compile(r'\baws_[a-z0-9_]+\b|\bprovider\s+"aws"\b')


class CostEstimator:
    """Produce a safe cost insight summary before apply."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name

    def estimate_apply_cost(
        self, command_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Estimate cost confidence for an apply operation.

        This intentionally avoids claiming exact price deltas when live pricing
        data, region context, or usage metrics are unavailable.
        """
        command_args = list(command_args or [])
        plan_file = self._extract_plan_file(command_args)

        if plan_file:
            return self._estimate_from_plan_file(plan_file)

        if self._aws_config_detected():
            return {
                "status": "warning",
                "title": "Cost preview unavailable",
                "summary": (
                    "AWS resources may be involved, but there is no saved plan file "
                    "and infra-guide does not perform live pricing lookups."
                ),
                "details": [
                    "Inference: exact monthly delta cannot be predicted safely from configuration alone.",
                    "Recommendation: run `infra-guide plan --out tfplan` first, then apply the saved plan.",
                    "Why this is limited: pricing depends on region, usage, storage class, transfer, and discounts.",
                ],
                "exact_estimate_available": False,
                "confidence": "low",
                "impact": "unknown",
            }

        return {
            "status": "info",
            "title": "Cost preview unavailable",
            "summary": (
                "No saved plan file was provided, so infra-guide cannot infer a reliable "
                "cost delta before apply."
            ),
            "details": [
                "If you are changing AWS infrastructure, save a plan first for a better impact summary.",
                "For other providers, infra-guide currently does not integrate with live pricing catalogs.",
            ],
            "exact_estimate_available": False,
            "confidence": "low",
            "impact": "unknown",
        }

    def _estimate_from_plan_file(self, plan_file: str) -> Dict[str, Any]:
        plan_json = self._load_plan_json(plan_file)
        if not plan_json:
            return {
                "status": "warning",
                "title": "Cost preview unavailable",
                "summary": (
                    f"Could not read saved plan file '{plan_file}' for cost analysis."
                ),
                "details": [
                    "Make sure the plan file exists and is readable by the current Terraform/OpenTofu binary.",
                ],
                "exact_estimate_available": False,
                "confidence": "low",
                "impact": "unknown",
            }

        resource_changes = plan_json.get("resource_changes", [])
        if not resource_changes:
            return {
                "status": "info",
                "title": "No infrastructure changes",
                "summary": "The saved plan does not contain resource changes.",
                "details": [
                    "No cost delta is expected from a no-op plan.",
                ],
                "exact_estimate_available": False,
                "confidence": "high",
                "impact": "none",
            }

        actions = Counter()
        providers = Counter()
        impactful_types = []
        aws_detected = False

        for item in resource_changes:
            action_tuple = tuple(item.get("change", {}).get("actions", []))
            action_label = self._normalize_action(action_tuple)
            actions[action_label] += 1

            provider_name = item.get("provider_name", "unknown")
            providers[self._short_provider_name(provider_name)] += 1

            resource_type = item.get("type", "unknown")
            if AWS_PROVIDER_TOKEN in provider_name or resource_type.startswith("aws_"):
                aws_detected = True
                impactful_types.append(resource_type)

        provider_summary = ", ".join(
            f"{provider} ({count})" for provider, count in providers.most_common(3)
        )
        top_types = Counter(impactful_types).most_common(4)

        if aws_detected:
            impact = self._classify_impact(impactful_types)
            detail_lines = [
                (
                    f"Plan summary: {actions.get('create', 0)} create, "
                    f"{actions.get('update', 0)} update, "
                    f"{actions.get('replace', 0)} replace, "
                    f"{actions.get('delete', 0)} delete."
                ),
                f"Top providers in plan: {provider_summary or 'aws'}",
            ]
            if top_types:
                detail_lines.append(
                    "Most likely cost-driving AWS resources: "
                    + ", ".join(f"{resource_type} x{count}" for resource_type, count in top_types)
                )
            detail_lines.extend(
                [
                    "Inference: this plan likely changes spend, but exact monthly delta cannot be predicted safely.",
                    "Missing inputs: live regional pricing, usage volume, transfer, storage growth, and discounts.",
                ]
            )
            return {
                "status": "warning",
                "title": "AWS cost impact detected",
                "summary": (
                    "A saved plan is available, but infra-guide still cannot promise an exact AWS "
                    "cost number without live pricing data."
                ),
                "details": detail_lines,
                "exact_estimate_available": False,
                "confidence": "low",
                "impact": impact,
            }

        return {
            "status": "info",
            "title": "Cost estimation not supported",
            "summary": (
                "The saved plan was analyzed, but current providers are outside infra-guide's "
                "cost heuristics."
            ),
            "details": [
                f"Top providers in plan: {provider_summary or 'unknown'}",
                "infra-guide currently only provides a conservative AWS-oriented cost impact hint.",
            ],
            "exact_estimate_available": False,
            "confidence": "low",
            "impact": "unknown",
        }

    def _extract_plan_file(self, command_args: List[str]) -> Optional[str]:
        skip_value_for_flags = {
            "-var",
            "-var-file",
            "-target",
            "-replace",
            "-lock-timeout",
            "-parallelism",
        }

        for index, argument in enumerate(command_args):
            if argument.startswith("-"):
                continue

            previous = command_args[index - 1] if index > 0 else ""
            if previous in skip_value_for_flags:
                continue

            if os.path.exists(argument):
                return argument
        return None

    def _aws_config_detected(self) -> bool:
        for filename in os.listdir("."):
            if not filename.endswith(".tf"):
                continue
            try:
                with open(filename, "r", encoding="utf-8", errors="ignore") as handle:
                    if AWS_CONFIG_PATTERN.search(handle.read()):
                        return True
            except OSError:
                continue
        return False

    def _load_plan_json(self, plan_file: str) -> Optional[Dict[str, Any]]:
        try:
            result = subprocess.run(
                [self.tool_name, "show", "-json", plan_file],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except Exception:
            return None

        if result.returncode != 0 or not result.stdout.strip():
            return None

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return None

    def _short_provider_name(self, provider_name: str) -> str:
        if "/" in provider_name:
            return provider_name.split("/")[-1]
        return provider_name

    def _normalize_action(self, action_tuple: tuple) -> str:
        if action_tuple == ("create",):
            return "create"
        if action_tuple == ("update",):
            return "update"
        if action_tuple == ("delete",):
            return "delete"
        if "create" in action_tuple and "delete" in action_tuple:
            return "replace"
        return "other"

    def _classify_impact(self, resource_types: List[str]) -> str:
        for resource_type in resource_types:
            if resource_type.startswith(HIGH_IMPACT_PREFIXES):
                return "high"
        for resource_type in resource_types:
            if resource_type.startswith(MEDIUM_IMPACT_PREFIXES):
                return "medium"
        return "low"
