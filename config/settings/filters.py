# SPDX-FileCopyrightText: 2025 Andrey Kotlyar
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Logging filters."""

import logging
import re
from typing import ClassVar

logger = logging.getLogger(__name__)


class SensitiveDataFilter(logging.Filter):
    """Logging filter that masks sensitive information in log messages.

    Replaces common secrets such as passwords, tokens, or access keys
    with placeholder values before the message is written to the log.
    """

    PATTERNS: ClassVar[list[tuple[re.Pattern[str], str]]] = [
        (re.compile(r"password=\S+"), "password=****"),
        (re.compile(r"token=\S+"), "token=****"),
        (re.compile(r"access=\S+"), "access=****"),
        (re.compile(r"refresh=\S+"), "refresh=****"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply the sensitive data filter to a log record.

        Replaces sensitive values (e.g., passwords or tokens) in the log
        message with masked placeholders. If an error occurs during
        processing, the method logs the error but still allows the
        record to pass through.

        Args:
            record (logging.LogRecord): The log record to process

        Returns:
            bool: Always return True to ensure the record is not dropped
        """
        if isinstance(record.msg, str):
            try:
                for pattern, replacement in self.PATTERNS:
                    record.msg = pattern.sub(replacement, record.msg)
            except Exception as e:
                logger.error(f"Error in SensitiveDataFilter: {e!s}")
        return True
