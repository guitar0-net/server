# SPDX-FileCopyrightText: 2025 Andrey Kotlyar
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import re
from unittest.mock import Mock, patch

import pytest

from config.settings.filters import SensitiveDataFilter


@pytest.fixture
def log_record() -> Mock:
    return Mock(spec=logging.LogRecord, msg="")


def test_sensitive_data_filter_normal(log_record: Mock) -> None:
    log_record.msg = "password=secret token=abc123 access=acc refresh=ref other"
    filter_ = SensitiveDataFilter()
    assert filter_.filter(log_record) is True
    assert log_record.msg == "password=**** token=**** access=**** refresh=**** other"


def test_sensitive_data_filter_non_string(log_record: Mock) -> None:
    allowed_value = 123
    log_record.msg = allowed_value
    filter_ = SensitiveDataFilter()
    assert filter_.filter(log_record) is True
    assert log_record.msg == allowed_value


def test_sensitive_data_filter_empty_string(log_record: Mock) -> None:
    log_record.msg = ""
    filter_ = SensitiveDataFilter()
    assert filter_.filter(log_record) is True
    assert not log_record.msg


def test_sensitive_data_filter_error_handling(
    log_record: Mock, caplog: pytest.LogCaptureFixture
) -> None:
    filter_ = SensitiveDataFilter()

    mock_pattern = Mock(spec=re.Pattern)
    mock_pattern.sub.side_effect = Exception("Regex error")

    mock_patterns = [(mock_pattern, "replacement")]

    log_record.msg = "password=123"

    with patch.object(filter_, "PATTERNS", mock_patterns):
        assert filter_.filter(log_record) is True
        assert log_record.msg == "password=123"

    assert any(
        "Error in SensitiveDataFilter: Regex error" in rec.message
        for rec in caplog.records
    )
    assert any(rec.levelname == "ERROR" for rec in caplog.records)
