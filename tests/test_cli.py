from argparse import Namespace

import pytest

from infra_guide.cli import (
    build_command_args,
    build_fmt_args,
    build_parser,
    clean_passthrough_args,
)


# ── clean_passthrough_args ────────────────────────────────────────────────────


def test_clean_passthrough_args_removes_separator():
    assert clean_passthrough_args(["--", "-target=module.network"]) == [
        "-target=module.network"
    ]


def test_clean_passthrough_args_empty():
    assert clean_passthrough_args([]) == []


def test_clean_passthrough_args_no_separator():
    assert clean_passthrough_args(["-compact-warnings"]) == ["-compact-warnings"]


# ── build_command_args ────────────────────────────────────────────────────────


def test_build_apply_command_args_supports_plan_file_and_auto_approve():
    args = Namespace(
        no_color=False,
        compact_warnings=False,
        show_sensitive=False,
        parallelism=None,
        lock_timeout=None,
        vars=["env=dev"],
        var_files=["env/dev.tfvars"],
        targets=["module.app"],
        yes=True,
        no_refresh=True,
        plan_file="tfplan",
        extra_args=["--", "-compact-warnings"],
    )

    command_args = build_command_args("apply", args)

    assert "-auto-approve" in command_args
    assert "-refresh=false" in command_args
    assert "tfplan" in command_args
    assert "-compact-warnings" in command_args


def test_build_destroy_args_auto_approve():
    args = Namespace(
        no_color=False,
        compact_warnings=False,
        show_sensitive=False,
        parallelism=None,
        lock_timeout=None,
        vars=[],
        var_files=[],
        targets=[],
        yes=True,
        no_refresh=False,
        extra_args=[],
    )
    cmd = build_command_args("destroy", args)
    assert "-auto-approve" in cmd


def test_build_plan_args_out_flag():
    args = Namespace(
        no_color=False,
        compact_warnings=False,
        show_sensitive=False,
        parallelism=None,
        lock_timeout=None,
        vars=[],
        var_files=[],
        targets=[],
        out="myplan",
        detailed_exitcode=False,
        destroy_mode=False,
        refresh_only=False,
        no_refresh=False,
        replacements=[],
        extra_args=[],
    )
    cmd = build_command_args("plan", args)
    assert "-out=myplan" in cmd


def test_build_plan_args_detailed_exitcode():
    args = Namespace(
        no_color=False,
        compact_warnings=False,
        show_sensitive=False,
        parallelism=None,
        lock_timeout=None,
        vars=[],
        var_files=[],
        targets=[],
        out=None,
        detailed_exitcode=True,
        destroy_mode=False,
        refresh_only=False,
        no_refresh=False,
        replacements=[],
        extra_args=[],
    )
    cmd = build_command_args("plan", args)
    assert "-detailed-exitcode" in cmd


# ── build_fmt_args ────────────────────────────────────────────────────────────


def test_build_fmt_args_defaults_to_recursive():
    args = Namespace(
        no_color=False,
        check=False,
        diff=False,
        no_recursive=False,
        extra_args=[],
    )

    assert build_fmt_args(args) == ["-recursive"]


def test_build_fmt_args_check_flag():
    args = Namespace(no_color=False, check=True, diff=False, no_recursive=False, extra_args=[])
    result = build_fmt_args(args)
    assert "-check" in result


def test_build_fmt_args_no_recursive_disables_recursive():
    args = Namespace(no_color=False, check=False, diff=False, no_recursive=True, extra_args=[])
    result = build_fmt_args(args)
    assert "-recursive" not in result


# ── build_parser ──────────────────────────────────────────────────────────────


def test_web_parser_supports_custom_port_and_no_browser():
    parser = build_parser()

    args = parser.parse_args(["web", "--port", "9000", "--no-browser"])

    assert args.command == "web"
    assert args.port == 9000
    assert args.no_browser is True


def test_completion_parser_accepts_bash():
    parser = build_parser()
    args = parser.parse_args(["completion", "bash"])
    assert args.command == "completion"
    assert args.shell == "bash"


def test_completion_parser_accepts_zsh():
    parser = build_parser()
    args = parser.parse_args(["completion", "zsh"])
    assert args.shell == "zsh"


def test_completion_parser_accepts_fish():
    parser = build_parser()
    args = parser.parse_args(["completion", "fish"])
    assert args.shell == "fish"


def test_completion_parser_rejects_invalid_shell():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["completion", "powershell"])


def test_theme_parser_set_valid_theme():
    parser = build_parser()
    args = parser.parse_args(["theme", "--set", "neon"])
    assert args.set_theme_name == "neon"


def test_plan_parser_target_flag():
    parser = build_parser()
    args = parser.parse_args(["plan", "--target", "module.vpc"])
    assert "module.vpc" in args.targets


def test_policy_parser_plan_file():
    parser = build_parser()
    args = parser.parse_args(["policy", "--plan-file", "plan.json"])
    assert args.policy_plan_file == "plan.json"
