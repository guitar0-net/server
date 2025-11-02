from collections.abc import Generator
from pathlib import Path

import pytest
from pydantic import ValidationError

from config.settings.base import Settings


@pytest.fixture
def env_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Generator[Path, None, None]:
    for var in ["SECRET_KEY", "DATABASE_URL", "DEBUG", "ENVIRONMENT", "ALLOWED_HOSTS"]:
        monkeypatch.delenv(var, raising=False)
    env_path = tmp_path / ".env.development"
    env_path.write_text(
        "\n".join([
            "SECRET_KEY=secret-key",
            "DATABASE_URL=sqlite:///db.sqlite3",
            "DEBUG=True",
            "ENVIRONMENT=development",
            """ALLOWED_HOSTS='["localhost","127.0.0.1"]'""",
        ])
    )
    monkeypatch.chdir(tmp_path)
    yield env_path


def test_settings_load_from_env(env_file: Path) -> None:
    settings = Settings(_env_file=env_file)  # pyright: ignore[reportCallIssue]
    assert settings.SECRET_KEY == "secret-key"
    assert settings.DATABASE_URL == "sqlite:///db.sqlite3"
    assert settings.DEBUG is True
    assert settings.ENVIRONMENT == "development"
    assert "localhost" in settings.ALLOWED_HOSTS


def test_settings_required_fields_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    for var in ["SECRET_KEY", "DATABASE_URL", "DEBUG", "ENVIRONMENT", "ALLOWED_HOSTS"]:
        monkeypatch.delenv(var, raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("Debug=False")
    with pytest.raises(ValidationError):
        Settings(_env_file=env_path)  # pyright: ignore[reportCallIssue]


def test_env_file_priority(monkeypatch: pytest.MonkeyPatch, env_file: Path) -> None:
    for var in ["SECRET_KEY", "DATABASE_URL", "DEBUG", "ENVIRONMENT", "ALLOWED_HOSTS"]:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("SECRET_KEY", "environment-secret-key")
    settings = Settings(_env_file=env_file)  # pyright: ignore[reportCallIssue]
    assert settings.SECRET_KEY == "environment-secret-key"
