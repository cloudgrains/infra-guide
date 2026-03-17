"""
Command execution module for running terraform/tofu commands.
"""

import shlex
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


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

    def execute_capture(
        self, command: str, additional_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a command and capture stdout/stderr for web or test consumers.

        Args:
            command: The command to execute
            additional_args: Additional arguments to pass to the command

        Returns:
            Dict[str, Any]: Structured execution result
        """
        cmd = self.build_command(command, additional_args)
        started_at = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
            duration_seconds = round(time.time() - started_at, 2)
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": self.format_command(command, additional_args),
                "duration_seconds": duration_seconds,
            }
        except KeyboardInterrupt:
            return {
                "success": False,
                "exit_code": 130,
                "stdout": "",
                "stderr": "Command interrupted by user.",
                "command": self.format_command(command, additional_args),
                "duration_seconds": round(time.time() - started_at, 2),
            }
        except Exception as error:
            return {
                "success": False,
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Error executing command: {error}",
                "command": self.format_command(command, additional_args),
                "duration_seconds": round(time.time() - started_at, 2),
            }

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
