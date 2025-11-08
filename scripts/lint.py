# SPDX-FileCopyrightText: 2025 Andrey Kotlyar
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Linting and type checking automation script.

Provides functions to run code formatters (Ruff), linters (Ruff), and type
checkers (Mypy) in a consistent and automated way.
"""

import subprocess
import sys


def run_command(command: list[str], name: str) -> None:
    """Run a subprocess command and handle failures.

    Executes the given command using subprocess.run and prints a header
    for clarity. If the command fails, prints an error message and exits
    the script.

    Args:
        command (list[str]): The command and arguments to execute.
        name (str): Human-readable name of the command for logging output.
    """
    print(f"{'=' * 33}{name}{'=' * 33}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print(f"{name} failed")
        sys.exit(1)


def main() -> None:
    """Run all linting and type checking commands sequentially.

    Executes Ruff formatting, Ruff linting with automatic fixes, and Mypy
    type checks in order.
    """
    run_command([sys.executable, "-m", "ruff", "format", "."], "Ruff Format")
    run_command([sys.executable, "-m", "ruff", "check", ".", "--fix"], "Ruff Check")
    run_command([sys.executable, "-m", "mypy", "."], "Mypy")


if __name__ == "__main__":
    main()
