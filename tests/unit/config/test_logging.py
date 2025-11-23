# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path

import pytest

from config.settings.base import Settings
from config.settings.logging import get_logging_config


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(
        SECRET_KEY="test",
        DATABASE_URL="sqlite:///:memory:",
        DEBUG=True,
        ENVIRONMENT="development",
    )


def test_logging_config_structure(mock_settings: Settings) -> None:
    config = get_logging_config(mock_settings)

    for key in ("handlers", "loggers", "formatters", "filters", "version"):
        assert key in config, f"Missing key '{key}' in logging config"

    assert isinstance(config["handlers"], dict)
    assert isinstance(config["loggers"], dict)
    assert isinstance(config["formatters"], dict)


def test_logging_loggers_exist(mock_settings: Settings) -> None:
    config = get_logging_config(mock_settings)
    loggers = config["loggers"]

    for logger_name in ["django", "rest_framework", "accounts"]:
        assert logger_name in loggers, f"Logger '{logger_name}' not configured"


def test_logging_loggers_levels(mock_settings: Settings) -> None:
    config = get_logging_config(mock_settings)
    loggers = config["loggers"]

    assert loggers["accounts"]["level"] == "DEBUG"
    assert loggers["django"]["level"] == "INFO"


def test_logging_file_handler_configuration(mock_settings: Settings) -> None:
    config = get_logging_config(mock_settings)
    handlers = config["handlers"]

    assert "file" in handlers, "File handler not found"
    file_handler = handlers["file"]

    # Проверка обязательных ключей
    required_keys = ["class", "filename", "maxBytes", "filters"]
    for key in required_keys:
        assert key in file_handler, f"'{key}' key missing in file handler"

    assert "class" in file_handler
    assert file_handler["class"] == "logging.handlers.RotatingFileHandler"
    assert "filename" in file_handler
    assert file_handler["filename"]
    assert Path(file_handler["filename"]).suffix == ".log"
    assert "maxBytes" in file_handler
    assert file_handler["maxBytes"]
    assert file_handler["maxBytes"] > 0
    assert "filters" in file_handler
    assert file_handler["filters"]
    assert "sensitive_data_filter" in file_handler["filters"]

    log_path = Path(file_handler["filename"])
    assert str(mock_settings.BASE_DIR) in str(log_path), (
        f"Log file path '{log_path}' must be under BASE_DIR"
    )


def test_logging_filters_exist(mock_settings: Settings) -> None:
    config = get_logging_config(mock_settings)
    filters = config["filters"]

    assert "sensitive_data_filter" in filters, "Missing sensitive_data_filter"
    assert "require_debug_false" in filters, "Missing require_debug_false"


def test_get_logging_config_prod(mock_settings: Settings) -> None:
    mock_settings.DEBUG = False
    mock_settings.ENVIRONMENT = "production"
    config = get_logging_config(mock_settings)
    assert config["loggers"]["accounts"]["level"] == "INFO"
