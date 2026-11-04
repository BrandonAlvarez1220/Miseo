import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_database_url_must_use_psycopg_driver() -> None:
    with pytest.raises(ValidationError, match="postgresql\\+psycopg"):
        Settings(database_url="postgresql://u:p@localhost/db")  # type: ignore[arg-type]


def test_cors_origins_accepts_comma_separated_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://a.test, http://b.test")
    settings = Settings(database_url="postgresql+psycopg://u:p@localhost/db")  # type: ignore[arg-type]
    assert settings.cors_origins == ["http://a.test", "http://b.test"]
