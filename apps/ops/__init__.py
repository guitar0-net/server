# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Operational surface of the app: endpoints the deployment talks to.

Holds the Prometheus registry and the metrics endpoint. This module is the
public API for metrics — other applications import from here rather than
using prometheus_client directly.
"""

from .registry import get_registry, reset_registry
