"""
Policy-as-code checker - validates infrastructure against defined policies.
"""

import json
import re
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


class PolicyChecker:
    """Validates infrastructure against security and compliance policies."""

    def __init__(self):
        """Initialize policy checker."""
        self.console = Console()
        self.policies = self._load_builtin_policies()

    def _load_builtin_policies(self) -> List[Dict[str, Any]]:
        """
        Load built-in security and compliance policies.

        Returns:
            List of policy rules
        """
        return [
            {
                "id": "no-public-s3",
                "name": "Prevent Public S3 Buckets",
                "severity": "high",
                "description": "S3 buckets should not be publicly accessible",
                "resource_type": "aws_s3_bucket",
                "check": lambda r: not r.get("acl", "").startswith("public")
            },
            {
                "id": "require-encryption",
                "name": "Require Encryption at Rest",
                "severity": "high",
                "description": "Resources should have encryption enabled",
                "resource_type": "aws_",
                "check": lambda r: r.get("encrypted") is True or 
                                 r.get("encryption") is not None or
                                 "kms_key" in r
            },
            {
                "id": "require-tags",
                "name": "Require Resource Tags",
                "severity": "medium",
                "description": "All resources should have required tags",
                "resource_type": "*",
                "check": lambda r: bool(r.get("tags", {}).get("Environment") and 
                                      r.get("tags", {}).get("Owner"))
            },
            {
                "id": "no-public-ingress",
                "name": "Prevent Wide-Open Security Groups",
                "severity": "critical",
                "description": "Security groups should not allow 0.0.0.0/0 ingress",
                "resource_type": "aws_security_group",
                "check": lambda r: not any(
                    rule.get("cidr_blocks", []) == ["0.0.0.0/0"] 
                    for rule in r.get("ingress", [])
                )
            },
            {
                "id": "require-versioning",
                "name": "S3 Bucket Versioning",
                "severity": "medium",
                "description": "S3 buckets should have versioning enabled",
                "resource_type": "aws_s3_bucket",
                "check": lambda r: r.get("versioning", {}).get("enabled") is True
            },
            {
                "id": "no-default-vpc",
                "name": "Avoid Default VPC Usage",
                "severity": "low",
                "description": "Resources should not use default VPC",
                "resource_type": "aws_",
                "check": lambda r: "default" not in str(r.get("vpc_id", "")).lower()
            }
        ]

    def check_plan(self, plan_json: str) -> Dict[str, Any]:
        """
        Check a plan against policies.

        Args:
            plan_json: JSON output from terraform/tofu plan

        Returns:
            Dict with policy check results
        """
        try:
            plan_data = json.loads(plan_json)
            violations = []
            passed = []

            resources = self._extract_resources(plan_data)

            for resource in resources:
                resource_type = resource.get("type", "")
                resource_name = resource.get("name", "")
                resource_values = resource.get("values", {})

                for policy in self.policies:
                    if not self._matches_resource_type(policy["resource_type"], resource_type):
                        continue

                    try:
                        if not policy["check"](resource_values):
                            violations.append({
                                "policy_id": policy["id"],
                                "policy_name": policy["name"],
                                "severity": policy["severity"],
                                "resource": f"{resource_type}.{resource_name}",
                                "description": policy["description"]
                            })
                        else:
                            passed.append({
                                "policy_id": policy["id"],
                                "resource": f"{resource_type}.{resource_name}"
                            })
                    except Exception:
                        # Policy check failed, skip
                        continue

            return {
                "success": True,
                "total_checks": len(passed) + len(violations),
                "passed": len(passed),
                "violations": len(violations),
                "violation_details": violations
            }

        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Invalid JSON plan output"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Policy check failed: {str(e)}"
            }

    def _extract_resources(self, plan_data: Dict) -> List[Dict]:
        """Extract resources from plan data."""
        resources = []
        
        # Handle different plan JSON formats
        if "resource_changes" in plan_data:
            for change in plan_data["resource_changes"]:
                if change.get("change", {}).get("actions") in [["create"], ["update"]]:
                    resources.append({
                        "type": change.get("type", ""),
                        "name": change.get("name", ""),
                        "values": change.get("change", {}).get("after", {})
                    })
        
        return resources

    def _matches_resource_type(self, policy_type: str, resource_type: str) -> bool:
        """Check if policy applies to resource type."""
        if policy_type == "*":
            return True
        return resource_type.startswith(policy_type)

    def show_policy_report(self, results: Dict[str, Any]):
        """
        Display policy check results.

        Args:
            results: Policy check results
        """
        if not results.get("success"):
            self.console.print(f"\n[bold red]❌ {results.get('error')}[/bold red]\n")
            return

        total = results.get("total_checks", 0)
        passed = results.get("passed", 0)
        violations = results.get("violations", 0)

        # Summary panel
        if violations == 0:
            summary = Panel(
                f"[bold green]✅ All Policy Checks Passed![/bold green]\n\n"
                f"[white]Checks Passed: {passed}/{total}[/white]",
                title="Policy Validation Report",
                border_style="green",
                box=box.ROUNDED
            )
        else:
            summary = Panel(
                f"[bold yellow]⚠️  Policy Violations Detected[/bold yellow]\n\n"
                f"[white]Passed: {passed}/{total}\n"
                f"Violations: {violations}/{total}[/white]",
                title="Policy Validation Report",
                border_style="yellow",
                box=box.ROUNDED
            )

        self.console.print()
        self.console.print(summary)
        self.console.print()

        if violations > 0:
            # Violations table
            table = Table(
                title="Policy Violations",
                show_header=True,
                header_style="bold red",
                box=box.ROUNDED
            )
            table.add_column("Severity", width=10)
            table.add_column("Policy", width=30)
            table.add_column("Resource", width=35)

            severity_colors = {
                "critical": "bold red",
                "high": "red",
                "medium": "yellow",
                "low": "blue"
            }

            for violation in results.get("violation_details", [])[:15]:
                severity = violation["severity"]
                color = severity_colors.get(severity, "white")
                
                table.add_row(
                    f"[{color}]{severity.upper()}[/{color}]",
                    violation["policy_name"],
                    violation["resource"]
                )

            self.console.print(table)
            self.console.print()
