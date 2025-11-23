# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import subprocess
from collections.abc import Generator

import pytest

from scripts import lint

type MockRun = list[list[str]]


@pytest.fixture
def mock_run(monkeypatch: pytest.MonkeyPatch) -> Generator[MockRun, None, None]:
    """Мок subprocess.run."""
    calls: MockRun = []

    def fake_run(command: list[str], check: bool) -> None:
        calls.append(command)
        if "ruff" in command or "mypy" in command:
            return
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", fake_run)
    yield calls


def test_run_command_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет, что run_command не падает при успешной команде."""

    def fake_run(command: list[str], check: bool) -> None:
        assert command == ["echo", "hello"]

    monkeypatch.setattr(subprocess, "run", fake_run)

    lint.run_command(["echo", "hello"], "Echo Test")


def test_run_command_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет, что run_command завершает процесс при ошибке."""

    def fake_run(command: list[str], check: bool) -> None:
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(SystemExit) as exc_info:
        lint.run_command(["false"], "Fail Test")

    assert exc_info.value.code == 1


def test_main_invokes_both_linters(mock_run: MockRun) -> None:
    """Проверяет, что main вызывает Ruff и Mypy в нужном порядке."""
    expected_amount_of_calls = 3
    lint.main()

    assert len(mock_run) == expected_amount_of_calls
    assert mock_run[0][2] == "ruff"
    assert mock_run[1][2] == "ruff"
    assert mock_run[2][2] == "mypy"


@pytest.mark.parametrize("failed_command", ("ruff", "mypy"))
def test_main_stops_on_failure(
    monkeypatch: pytest.MonkeyPatch, failed_command: str
) -> None:
    """Проверяет, что main прекращает работу при ошибке Mypy."""

    def fake_run(command: list[str], check: bool) -> None:
        if failed_command in command:
            raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(SystemExit):
        lint.main()
