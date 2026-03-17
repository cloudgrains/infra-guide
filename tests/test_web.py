from infra_guide.preferences import PreferencesStore
from infra_guide.web import WebCommandCenterBackend


class DummyInspector:
    def inspect(self, include_state=False):
        return {
            "cwd": "/tmp/app",
            "workspace": "default",
            "readiness": "ready",
            "readiness_label": "Ready to operate",
            "recommendation": "Run doctor, plan, then apply.",
            "tf_file_count": 4,
            "tfvars_file_count": 1,
            "module_block_count": 2,
            "backend_configured": True,
            "lock_file_present": True,
            "state_present": True if include_state else None,
        }


class DummyRunner:
    def format_command(self, command_name, args):
        if args:
            return "tofu {0} {1}".format(command_name, " ".join(args))
        return "tofu {0}".format(command_name)

    def execute_capture(self, command_name, args):
        return {
            "success": True,
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "command": self.format_command(command_name, args),
            "duration_seconds": 0.2,
        }


class DummyStateExplorer:
    def list_resources(self):
        return [{"address": "aws_instance.web", "type": "aws_instance"}]

    def get_state_stats(self):
        return {
            "total_resources": 1,
            "resource_types": 1,
            "has_state": True,
            "terraform_version": "1.7.0",
        }

    def show_resource_detail(self, resource_address):
        if resource_address == "aws_instance.web":
            return 'id = "i-123456"'
        return None


class DummyWorkspaceManager:
    def list_workspaces(self):
        return {
            "success": True,
            "workspaces": ["default", "dev"],
            "current": "default",
            "count": 2,
        }

    def create_workspace(self, name):
        return {"success": True, "exit_code": 0, "stdout": name, "stderr": ""}

    def select_workspace(self, name):
        return {"success": True, "exit_code": 0, "stdout": name, "stderr": ""}

    def delete_workspace(self, name):
        return {"success": True, "exit_code": 0, "stdout": name, "stderr": ""}


class DummyValidator:
    def run_all_checks(self):
        return {
            "checks": [
                {
                    "name": "Configuration Files",
                    "status": "pass",
                    "message": "Found 4 .tf file(s)",
                }
            ],
            "total": 1,
            "passed": 1,
            "warnings": 0,
            "failed": 0,
            "all_passed": True,
        }


class DummyDriftDetector:
    def detect_drift(self):
        return {
            "success": True,
            "drift_detected": False,
            "drift_count": 0,
            "drifted_resources": [],
        }


class DummyCICDRunner:
    def run_pipeline_capture(self, skip_init=False, skip_validation=False, output_file="tfplan"):
        return {
            "success": True,
            "steps": [],
            "plan_file": output_file,
            "has_changes": False,
        }


class DummyCostEstimator:
    def estimate_apply_cost(self, command_args=None):
        return {
            "status": "warning",
            "title": "Cost preview unavailable",
            "summary": "Plan data is missing.",
            "details": ["Run plan --out tfplan first."],
            "exact_estimate_available": False,
            "confidence": "low",
            "impact": "unknown",
        }


def build_backend(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    preferences = PreferencesStore()
    services = {
        "inspector": DummyInspector(),
        "runner": DummyRunner(),
        "state_explorer": DummyStateExplorer(),
        "workspace_manager": DummyWorkspaceManager(),
        "validator": DummyValidator(),
        "drift_detector": DummyDriftDetector(),
        "cicd_runner": DummyCICDRunner(),
        "cost_estimator": DummyCostEstimator(),
        "preferences": preferences,
    }
    return WebCommandCenterBackend("tofu", "OpenTofu v1.0.0", services)


def test_web_backend_context_includes_theme_and_state(monkeypatch, tmp_path):
    backend = build_backend(monkeypatch, tmp_path)

    context = backend.get_context()

    assert context["theme_name"] == "aurora"
    assert context["state"]["resource_count"] == 1
    assert context["runner_commands"][0]["name"] == "init"


def test_web_backend_requires_confirmation_for_apply(monkeypatch, tmp_path):
    backend = build_backend(monkeypatch, tmp_path)

    result = backend.run_command("apply", "--plan-file tfplan", confirm_execution=False)

    assert result["success"] is False
    assert result["exit_code"] == 2


def test_web_backend_records_runner_history(monkeypatch, tmp_path):
    backend = build_backend(monkeypatch, tmp_path)

    result = backend.run_command("plan", "--out tfplan", confirm_execution=False)
    history = backend.services["preferences"].get_history(limit=1)

    assert result["success"] is True
    assert history[0]["command_name"] == "plan"
    assert history[0]["args"] == ["-out=tfplan"]
