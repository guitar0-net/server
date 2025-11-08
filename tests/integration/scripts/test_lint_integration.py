# SPDX-FileCopyrightText: 2025 Andrey Kotlyar
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import runpy
from pathlib import Path

import pytest


@pytest.mark.integration
def test_run_module_executes_main(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Integrity test scripts/lint.py."""
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "lint.py"

    runpy.run_path(str(script_path), run_name="__main__")

    captured = capsys.readouterr()
    assert "=" * 33 + "Ruff Format" + "=" * 33 in captured.out
    assert "=" * 33 + "Ruff Check" + "=" * 33 in captured.out
    assert "=" * 33 + "Mypy" + "=" * 33 in captured.out
