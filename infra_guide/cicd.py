"""
CI/CD mode - non-interactive execution for continuous integration pipelines.
"""

import sys
import subprocess
import json
from typing import Dict, Any, List, Optional
from rich.console import Console


class CICDRunner:
    """Non-interactive runner for CI/CD pipelines."""

    def __init__(self, tool_name: str):
        """
        Initialize CI/CD runner.

        Args:
            tool_name: The IaC tool name ('terraform' or 'tofu')
        """
        self.tool_name = tool_name
        self.console = Console()

    def run_command(self, command: str, auto_approve: bool = False,
                   detailed_exitcode: bool = False, json_output: bool = False,
                   extra_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run command in CI/CD-safe mode (non-interactive).

        Args:
            command: Command to run ('init', 'plan', 'apply', etc.)
            auto_approve: Whether to auto-approve (for apply/destroy)
            detailed_exitcode: Use detailed exit codes
            json_output: Request JSON output where supported
            extra_args: Additional arguments to pass through

        Returns:
            Dict with execution results
        """
        cmd = [self.tool_name, command]

        # Add CI/CD-friendly flags
        if command in ['apply', 'destroy'] and auto_approve:
            cmd.append('-auto-approve')

        if command == 'plan' and detailed_exitcode:
            cmd.append('-detailed-exitcode')

        if json_output and command in ['plan', 'show', 'validate']:
            cmd.append('-json')

        # Always use -input=false for non-interactive mode
        if command in ['init', 'plan', 'apply', 'destroy']:
            cmd.append('-input=false')

        if extra_args:
            cmd.extend(extra_args)

        # Capture output
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout for long operations
            )

            success_codes = {0}
            if command == 'plan' and detailed_exitcode:
                success_codes = {0, 2}

            return {
                "success": result.returncode in success_codes,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": ' '.join(cmd),
                "has_changes": command == 'plan' and detailed_exitcode and result.returncode == 2
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "error": "Command timed out after 1 hour"
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "error": f"Failed to execute: {str(e)}"
            }

    def validate_pipeline(self) -> Dict[str, Any]:
        """
        Run validation suitable for CI/CD pipelines.

        Returns:
            Dict with validation results
        """
        results = {
            "checks": [],
            "all_passed": True
        }

        # Check 1: Validate syntax
        validate_result = self.run_command('validate', json_output=True)
        if validate_result["success"]:
            results["checks"].append({
                "name": "Syntax Validation",
                "passed": True,
                "message": "Configuration is valid"
            })
        else:
            results["checks"].append({
                "name": "Syntax Validation",
                "passed": False,
                "message": "Configuration has errors",
                "details": validate_result.get("stderr", "")
            })
            results["all_passed"] = False

        # Check 2: Format check
        fmt_result = subprocess.run(
            [self.tool_name, 'fmt', '-check', '-recursive'],
            capture_output=True,
            text=True
        )
        
        if fmt_result.returncode == 0:
            results["checks"].append({
                "name": "Format Check",
                "passed": True,
                "message": "All files are properly formatted"
            })
        else:
            results["checks"].append({
                "name": "Format Check",
                "passed": False,
                "message": "Files need formatting",
                "details": fmt_result.stdout
            })
            results["all_passed"] = False

        return results

    def plan_with_output(self, output_file: str = "tfplan") -> Dict[str, Any]:
        """
        Run plan and save to file (CI/CD pattern).

        Args:
            output_file: Path to save plan file

        Returns:
            Dict with plan results
        """
        result = self.run_command(
            'plan',
            detailed_exitcode=True,
            extra_args=[f'-out={output_file}']
        )

        if result["success"]:
            result["plan_file"] = output_file

        return result

    def apply_from_plan(self, plan_file: str) -> Dict[str, Any]:
        """
        Apply a saved plan file (CI/CD pattern).

        Args:
            plan_file: Path to plan file

        Returns:
            Dict with apply results
        """
        cmd = [self.tool_name, 'apply', '-input=false', plan_file]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )

            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "error": f"Failed to apply plan: {str(e)}"
            }

    def print_cicd_result(self, result: Dict[str, Any]):
        """
        Print results in CI/CD-friendly format.

        Args:
            result: Result dictionary
        """
        if result.get("success"):
            self.console.print(f"[green]✓[/green] Command succeeded")
            self.console.print(f"Exit code: {result.get('exit_code', 0)}")
        else:
            self.console.print(f"[red]✗[/red] Command failed")
            self.console.print(f"Exit code: {result.get('exit_code', -1)}")
            
            if result.get("error"):
                self.console.print(f"Error: {result['error']}")
            
            if result.get("stderr"):
                self.console.print("\nStderr output:")
                self.console.print(result["stderr"])

        sys.exit(result.get('exit_code', 1 if not result.get("success") else 0))

    def run_full_pipeline(self, skip_init: bool = False, 
                         skip_validation: bool = False) -> bool:
        """
        Run a complete CI/CD pipeline.

        Args:
            skip_init: Skip initialization step
            skip_validation: Skip validation checks

        Returns:
            True if all steps passed
        """
        self.console.print("[bold cyan]Running CI/CD Pipeline[/bold cyan]\n")

        # Step 1: Init
        if not skip_init:
            self.console.print("Step 1: Initialization...")
            init_result = self.run_command('init')
            if not init_result["success"]:
                self.console.print("[red]✗ Init failed[/red]")
                return False
            self.console.print("[green]✓ Init succeeded[/green]\n")

        # Step 2: Validation
        if not skip_validation:
            self.console.print("Step 2: Validation...")
            validate_result = self.validate_pipeline()
            if not validate_result["all_passed"]:
                self.console.print("[red]✗ Validation failed[/red]")
                for check in validate_result["checks"]:
                    if not check["passed"]:
                        self.console.print(f"  - {check['name']}: {check['message']}")
                return False
            self.console.print("[green]✓ Validation succeeded[/green]\n")

        # Step 3: Plan
        self.console.print("Step 3: Plan...")
        plan_result = self.plan_with_output()
        if not plan_result["success"]:
            self.console.print("[red]✗ Plan failed[/red]")
            return False
        
        has_changes = plan_result.get("has_changes", False)
        if has_changes:
            self.console.print("[yellow]⚠ Plan has changes[/yellow]\n")
        else:
            self.console.print("[green]✓ Plan succeeded (no changes)[/green]\n")

        self.console.print("[bold green]✓ Pipeline completed successfully[/bold green]")
        return True

    def run_pipeline_capture(
        self,
        skip_init: bool = False,
        skip_validation: bool = False,
        output_file: str = "tfplan",
    ) -> Dict[str, Any]:
        """
        Run the CI/CD pipeline without printing and return structured step results.

        Args:
            skip_init: Skip initialization step
            skip_validation: Skip validation checks
            output_file: Saved plan filename

        Returns:
            Dict with overall status and step details
        """
        steps = []

        if not skip_init:
            init_result = self.run_command("init")
            steps.append(
                {
                    "name": "init",
                    "success": init_result["success"],
                    "details": init_result,
                }
            )
            if not init_result["success"]:
                return {"success": False, "steps": steps}

        if not skip_validation:
            validation_result = self.validate_pipeline()
            steps.append(
                {
                    "name": "validate",
                    "success": validation_result["all_passed"],
                    "details": validation_result,
                }
            )
            if not validation_result["all_passed"]:
                return {"success": False, "steps": steps}

        plan_result = self.plan_with_output(output_file=output_file)
        steps.append(
            {
                "name": "plan",
                "success": plan_result["success"],
                "details": plan_result,
            }
        )

        return {
            "success": plan_result["success"],
            "steps": steps,
            "plan_file": output_file,
            "has_changes": plan_result.get("has_changes", False),
        }
