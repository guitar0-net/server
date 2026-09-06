# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Prometheus registry management.

Metrics are defined against the singleton registry. A scrape renders that same
registry, or — under ``PROMETHEUS_MULTIPROC_DIR`` — a throwaway one merging the
mmap files of every worker, so it describes the whole app and not the single
worker that answered.
"""

import os
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry

_registry: "CollectorRegistry | None" = None
_lock = threading.Lock()


def _multiprocess_enabled() -> bool:
    """Check whether prometheus_client shares values through mmap files.

    Returns:
        True when PROMETHEUS_MULTIPROC_DIR is set in the environment.
    """
    return bool(os.environ.get("PROMETHEUS_MULTIPROC_DIR"))


def get_registry() -> "CollectorRegistry":
    """Get or create the singleton CollectorRegistry.

    Uses double-checked locking for thread-safe lazy initialization.

    Returns:
        The singleton CollectorRegistry instance.
    """
    global _registry  # noqa: PLW0603

    if _registry is None:
        with _lock:
            if _registry is None:
                from prometheus_client import CollectorRegistry  # noqa: PLC0415

                _registry = CollectorRegistry()
    return _registry


def build_exposition_registry() -> "CollectorRegistry":
    """Build the registry that one /metrics/ scrape should render.

    Returns:
        The singleton registry, or a fresh multiprocess one per scrape.
    """
    if not _multiprocess_enabled():
        return get_registry()

    from prometheus_client import CollectorRegistry, multiprocess  # noqa: PLC0415

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return registry


def reset_registry() -> None:
    """Reset the registry singleton. Only for testing."""
    global _registry  # noqa: PLW0603

    with _lock:
        _registry = None
