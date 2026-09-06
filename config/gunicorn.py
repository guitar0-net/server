# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Gunicorn configuration for production deployment."""

import multiprocessing
import os
import shutil
from pathlib import Path
from typing import Protocol


class _Worker(Protocol):
    """The part of a gunicorn worker object the hooks below touch."""

    pid: int


# Wiped on boot: prometheus_client never expires these files, so values from
# a previous run would be summed into the new ones.
PROMETHEUS_MULTIPROC_DIR = os.getenv("PROMETHEUS_MULTIPROC_DIR")
if PROMETHEUS_MULTIPROC_DIR:
    shutil.rmtree(PROMETHEUS_MULTIPROC_DIR, ignore_errors=True)
    Path(PROMETHEUS_MULTIPROC_DIR).mkdir(parents=True, exist_ok=True)

# Bind to all interfaces on port 8000
bind = "0.0.0.0:8000"

# Worker configuration
# Recommended formula: 2 * CPU cores + 1
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
timeout = 30
keepalive = 2

# tmpfs for the worker heartbeat: a slow write on overlayfs makes the arbiter
# kill healthy workers. nosec B108 — gunicorn creates the file with mkstemp()
# and unlinks it at once, so there is no predictable path to hijack.
worker_tmp_dir = "/dev/shm"  # nosec B108

# Recycling off: every worker pid leaves mmap files that are never reclaimed.
max_requests = 0

# Logging
accesslog = "-"  # stdout
errorlog = "-"  # stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Put the level first so the error/boot log lines match the same
# `{levelname} {message}` shape as Django's console formatter — the log
# pipeline (Grafana Alloy) detects level by matching the start of the line.
#
# "loggers" replaces gunicorn's default mapping wholesale, so both are listed.
logconfig_dict = {
    "formatters": {
        "generic": {
            "format": "{levelname} {asctime} [{process}] {message}",
            "style": "{",
        },
    },
    "loggers": {
        "gunicorn.error": {
            "level": "INFO",
            "handlers": ["error_console"],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

# Process naming
proc_name = "guitar0-backend"

# Graceful timeout
graceful_timeout = 30

# Preload app for faster worker spawning (uses more memory)
preload_app = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190


def child_exit(server: object, worker: _Worker) -> None:
    """Release the exiting worker's Prometheus gauge files.

    Without it a dead worker keeps contributing to `livesum` aggregates.

    Args:
        server: The gunicorn arbiter that reaped the worker.
        worker: The worker that has just exited.
    """
    if not PROMETHEUS_MULTIPROC_DIR:
        return

    from prometheus_client import multiprocess  # noqa: PLC0415

    multiprocess.mark_process_dead(worker.pid)
