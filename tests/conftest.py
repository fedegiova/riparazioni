"""Shared pytest fixtures."""

import pytest
from sqlalchemy.pool import StaticPool

from app import create_app


@pytest.fixture()
def app(tmp_path):
    """Application under test: in-memory SQLite, isolated runtime dirs."""
    app = create_app("testing")
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_ENGINE_OPTIONS={
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        },
        UPLOAD_DIR=tmp_path / "uploads",
        LOG_DIR=tmp_path / "log",
    )
    with app.app_context():
        yield app


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()
