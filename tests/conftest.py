"""Shared pytest fixtures for infra-guide tests."""

import pytest


class FakeCompletedProcess:
    """Minimal subprocess.CompletedProcess substitute."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture()
def fake_run_ok():
    """Return a factory that produces successful subprocess stubs."""

    def _factory(stdout="", stderr="", returncode=0):
        return FakeCompletedProcess(returncode=returncode, stdout=stdout, stderr=stderr)

    return _factory


@pytest.fixture()
def tmp_workspace(tmp_path):
    """A temporary directory with a minimal .tf file and .terraform dir."""
    tf = tmp_path / "main.tf"
    tf.write_text('provider "aws" {}\n')
    (tmp_path / ".terraform").mkdir()
    (tmp_path / ".terraform.lock.hcl").write_text("# lock\n")
    return tmp_path


@pytest.fixture()
def tmp_empty_workspace(tmp_path):
    """A temporary directory with no .tf files."""
    return tmp_path
