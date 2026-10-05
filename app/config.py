"""Application configuration.

Every setting is read from the environment; a local ``.env`` file is loaded
by ``app/__init__.py`` before these values are evaluated. See
``.env.example`` for the full list of variables.
"""

import os
from pathlib import Path

# Repository root: the directory that contains the ``app`` package.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

_BASE_DIR = Path(os.environ.get("BASE_DIR") or PROJECT_ROOT)


def _env(name: str, default: str | None = None) -> str | None:
    """Return an environment variable, or *default* when unset/empty."""
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def _bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    """Settings shared by every environment."""

    SECRET_KEY = _env("SECRET_KEY", "dev-only-secret-key")

    DEBUG = _bool("FLASK_DEBUG", False)
    TESTING = False

    # MSSQL via pyodbc. URL form:
    # mssql+pyodbc://USER:PASSWORD@HOST:1433/DB?driver=ODBC+Driver+18+for+SQL+Server
    SQLALCHEMY_DATABASE_URI = _env(
        "DATABASE_URL",
        "mssql+pyodbc://sa:YourStrong%28Pass%29123@localhost:1433/riparazioni"
        "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes",
    )

    # Track modifications for the SQLAlchemy session.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Writable runtime directories.
    BASE_DIR = _BASE_DIR
    UPLOAD_DIR = Path(_env("UPLOAD_DIR", str(_BASE_DIR / "var" / "uploads")))
    LOG_DIR = Path(_env("LOG_DIR", str(_BASE_DIR / "var" / "log")))


class DevelopmentConfig(BaseConfig):
    """Local development (``flask run``)."""


class TestingConfig(BaseConfig):
    """Test suite. Uses an in-memory SQLite database unless TEST_DATABASE_URL
    points somewhere else, so the tests run without a live MSSQL server."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _env("TEST_DATABASE_URL", "sqlite://")


class ProductionConfig(BaseConfig):
    """Linux server (gunicorn + systemd)."""

    DEBUG = False
