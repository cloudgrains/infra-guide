from argparse import Namespace

from infra_guide.cli import build_command_args, build_fmt_args, clean_passthrough_args


def test_clean_passthrough_args_removes_separator():
    assert clean_passthrough_args(["--", "-target=module.network"]) == [
        "-target=module.network"
    ]


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


def test_build_fmt_args_defaults_to_recursive():
    args = Namespace(
        no_color=False,
        check=False,
        diff=False,
        no_recursive=False,
        extra_args=[],
    )

    assert build_fmt_args(args) == ["-recursive"]
