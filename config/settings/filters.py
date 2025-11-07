# SPDX-FileCopyrightText: 2025 Andrey Kotlyar
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import re
from typing import ClassVar

logger = logging.getLogger(__name__)


class SensitiveDataFilter(logging.Filter):
    PATTERNS: ClassVar[list[tuple[re.Pattern[str], str]]] = [
        (re.compile(r"password=\S+"), "password=****"),
        (re.compile(r"token=\S+"), "token=****"),
        (re.compile(r"access=\S+"), "access=****"),
        (re.compile(r"refresh=\S+"), "refresh=****"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            try:
                for pattern, replacement in self.PATTERNS:
                    record.msg = pattern.sub(replacement, record.msg)
            except Exception as e:
                logger.error(f"Error in SensitiveDataFilter: {e!s}")
        return True
