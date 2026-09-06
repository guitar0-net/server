# SPDX-FileCopyrightText: 2025-2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the metrics registry singleton."""

import importlib
import threading
from collections.abc import Generator
from pathlib import Path
from types import TracebackType
from unittest.mock import patch
from uuid import uuid4

import pytest
from prometheus_client import CollectorRegistry, Counter

from apps.ops.registry import (
    build_exposition_registry,
    get_registry,
    reset_registry,
)


@pytest.fixture(autouse=True)
def isolate_registry() -> Generator[None]:
    """Isolate each test by resetting registry before and after."""
    from apps.ops import metrics as metrics_module

    reset_registry()
    importlib.reload(metrics_module)
    yield
    reset_registry()
    importlib.reload(metrics_module)


def test_get_registry_returns_same_instance_on_multiple_calls() -> None:
    registry1 = get_registry()
    registry2 = get_registry()
    assert registry1 is registry2


def test_get_registry_thread_safety() -> None:
    """Test that get_registry is thread-safe."""
    registries: list[CollectorRegistry] = []
    errors: list[Exception] = []

    def get_registry_thread() -> None:
        try:
            registries.append(get_registry())
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=get_registry_thread) for _ in range(10)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(errors) == 0
    assert len(registries) == 10
    assert all(r is registries[0] for r in registries)


def test_reset_registry_creates_new_instance() -> None:
    registry1 = get_registry()
    reset_registry()
    registry2 = get_registry()
    assert registry1 is not registry2


def test_reset_registry_allows_reregistration() -> None:
    """Test that resetting allows metrics to be registered again."""
    registry1 = get_registry()
    Counter(
        name="test_counter_unique",
        documentation="Test counter",
        registry=registry1,
    )

    reset_registry()

    registry2 = get_registry()
    counter = Counter(
        name="test_counter_unique",
        documentation="Test counter",
        registry=registry2,
    )
    assert counter is not None


def test_double_checked_locking_inner_check_returns_existing_registry() -> None:
    """Test the inner None check in double-checked locking.

    This covers the branch where a thread enters the lock
    but _registry is already set (by another thread).
    """
    import apps.ops.registry as registry_module

    reset_registry()

    existing_registry = CollectorRegistry()

    original_lock = registry_module._lock
    call_count = 0

    class MockLock:
        def __enter__(self) -> None:
            nonlocal call_count
            call_count += 1
            original_lock.__enter__()
            registry_module._registry = existing_registry

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ) -> None:
            original_lock.__exit__(exc_type, exc_val, exc_tb)

    with patch.object(registry_module, "_lock", MockLock()):
        registry_module._registry = None
        result = get_registry()

    assert result is existing_registry
    assert call_count == 1


@pytest.fixture
def multiproc_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point PROMETHEUS_MULTIPROC_DIR at an empty directory of its own."""
    directory = tmp_path / f"метрики-{uuid4().hex[:8]}"
    directory.mkdir()
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", str(directory))
    return directory


def test_build_exposition_registry_serves_the_singleton_without_multiproc_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PROMETHEUS_MULTIPROC_DIR", raising=False)
    assert build_exposition_registry() is get_registry()


def test_build_exposition_registry_dont_expose_the_singleton_in_multiprocess_mode(
    multiproc_dir: Path,
) -> None:
    assert build_exposition_registry() is not get_registry()


def test_build_exposition_registry_builds_one_registry_per_scrape_in_multiprocess_mode(
    multiproc_dir: Path,
) -> None:
    assert build_exposition_registry() is not build_exposition_registry()
