"""Tests for shell completion scripts."""

import pytest
from infra_guide.completion import get_completion_script


def test_bash_script_contains_complete_command():
    script = get_completion_script("bash")
    assert "complete -F _infra_guide_completion infra-guide" in script


def test_bash_script_contains_all_subcommands():
    script = get_completion_script("bash")
    for cmd in ("init", "plan", "apply", "destroy", "doctor", "completion"):
        assert cmd in script


def test_zsh_script_has_compdef():
    script = get_completion_script("zsh")
    assert "#compdef infra-guide" in script


def test_fish_script_has_complete_commands():
    script = get_completion_script("fish")
    assert "complete -c infra-guide" in script


def test_fish_script_lists_completion_shells():
    script = get_completion_script("fish")
    assert "bash zsh fish" in script


def test_all_shells_return_strings():
    for shell in ("bash", "zsh", "fish"):
        result = get_completion_script(shell)
        assert isinstance(result, str)
        assert len(result) > 100


def test_unsupported_shell_raises_value_error():
    with pytest.raises(ValueError, match="Unsupported shell"):
        get_completion_script("powershell")


def test_bash_includes_theme_names():
    from infra_guide.preferences import THEMES

    script = get_completion_script("bash")
    for theme in THEMES:
        assert theme in script
