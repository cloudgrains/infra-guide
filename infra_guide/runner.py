"""
Command execution module for running terraform/tofu commands.
"""

import shlex
import subprocess
import sys
from typing import List, Optional


class CommandRunner:
    """Executes terraform/tofu commands."""

    def __init__(self, tool_name: str):
        """
        Initialize the command runner.

        Args:
            tool_name: Name of the tool to use ('tofu' or 'terraform')
        """
        self.tool_name = tool_name

    def build_command(
        self, command: str, additional_args: Optional[List[str]] = None
    ) -> List[str]:
        """
        Build the final command list.

        Args:
            command: The subcommand to execute
            additional_args: Extra arguments to append

        Returns:
            List[str]: Command parts suitable for subprocess
        """
        cmd = [self.tool_name, command]
        if additional_args:
            cmd.extend(additional_args)
        return cmd

    def format_command(
        self, command: str, additional_args: Optional[List[str]] = None
    ) -> str:
        """
        Return a shell-safe command preview string.

        Args:
            command: The subcommand to execute
            additional_args: Extra arguments to append

        Returns:
            str: Shell-friendly command preview
        """
        cmd = self.build_command(command, additional_args)
        try:
            return shlex.join(cmd)
        except AttributeError:
            return " ".join(shlex.quote(part) for part in cmd)

    def execute(self, command: str, additional_args: Optional[list] = None) -> int:
        """
        Execute a terraform/tofu command.

        Args:
            command: The command to execute (e.g., 'init', 'plan', 'apply')
            additional_args: Additional arguments to pass to the command

        Returns:
            int: Return code from the command (0 for success)
        """
        cmd = self.build_command(command, additional_args)

        try:
            # Run the command with live output
            result = subprocess.run(
                cmd,
                stdout=sys.stdout,
                stderr=sys.stderr,
                stdin=sys.stdin
            )
            return result.returncode
        except KeyboardInterrupt:
            print("\n\nCommand interrupted by user.")
            return 130  # Standard interrupt exit code
        except Exception as e:
            print(f"\n\nError executing command: {e}")
            return 1

    def execute_with_flags(self, command: str, flags: dict) -> int:
        """
        Execute a command with specific flags.

        Args:
            command: The command to execute
            flags: Dictionary of flags to apply

        Returns:
            int: Return code from the command
        """
        additional_args = []
        for flag, value in flags.items():
            if value is True:
                additional_args.append(flag)
            elif value:
                additional_args.extend([flag, str(value)])

        return self.execute(command, additional_args)
