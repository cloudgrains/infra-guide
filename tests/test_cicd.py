from infra_guide.cicd import CICDRunner


class CompletedProcessStub:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_command_accepts_detailed_exit_code_two(monkeypatch):
    def fake_run(*args, **kwargs):
        return CompletedProcessStub(returncode=2, stdout="changes", stderr="")

    monkeypatch.setattr("infra_guide.cicd.subprocess.run", fake_run)

    runner = CICDRunner("tofu")
    result = runner.run_command("plan", detailed_exitcode=True)

    assert result["success"] is True
    assert result["has_changes"] is True
    assert result["exit_code"] == 2
