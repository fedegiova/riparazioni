"""Shared pytest fixtures.

The test database is in-memory SQLite. The pre-existing ``DATIDBSTORICO``
objects (owned by the legacy system) live in a separate attached in-memory
database named ``DATIDBSTORICO`` so their ``schema="DATIDBSTORICO"`` table
mappings resolve to real tables without any statement rewriting.

SQLite does not enforce foreign keys that cross attached databases, so the
owned→external FKs (``REPAIRS.customer`` → VICLIENTI, ``REPAIRS.vehicle`` →
TBALLESTIMENTI) are validated in the service layer, exactly as they are
enforced in production (MSSQL forbids FKs to views; the customer reference
is checked in code and surfaced as HTTP 409).
"""

import pytest
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

from app import create_app


def _create_test_app(tmp_path):
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
    return app


@pytest.fixture()
def app(tmp_path):
    """Application under test: in-memory SQLite, isolated runtime dirs."""
    app = _create_test_app(tmp_path)
    with app.app_context():
        yield app


@pytest.fixture()
def client(app, db):
    """Flask test client backed by a ready in-memory database."""
    return app.test_client()


@pytest.fixture()
def db(app):
    """In-memory SQLite with owned + external tables, FKs on, and seed rows.

    Yields the ``db`` extension; leaves a committed session usable by tests.
    """
    from app import models  # noqa: F401  (register mappings on the metadata)
    from app.extensions import db as dbext
    from app.models import AppUser, Customer, Vehicle

    @event.listens_for(dbext.engine, "connect")
    def _setup_connection(dbapi_connection, connection_record):
        # Give the external (legacy) schema a real database in SQLite.
        dbapi_connection.execute("ATTACH DATABASE ':memory:' AS DATIDBSTORICO")
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    # The fixture runs inside the app context pushed by the `app` fixture,
    # so the extension's engine/session are usable directly.
    dbext.metadata.create_all(dbext.engine)

    vehicle = Vehicle(
        ID_INT=1,
        ID="000000000000001",
        NOMINATIVO_ID="NOM0000000000001",
        TARGA="ABC123",
        AUTOCARRO="FIAT",
        CARROZZERIA="FURGONE",
        MODELLO="DUCATO",
        CLASSE="N1",
        PROGRESSIVO=1,
    )
    customer = Customer(
        ID=1,
        N_NOMINATIVO=1,
        CLIENTE="ACME SRL",
        NCLIENTE="C001",
        VIA="VIA ROMA 1",
        CAP="10100",
        CITTA="TORINO",
        PROV="TO",
        TEL="0110000000",
        CELL="3330000000",
        EMAIL="ACME@EXAMPLE.COM",
    )
    user = AppUser(ID_INT=1, ID="000000000000001", NAME="OPERATOR", PASSWORD="hash")
    dbext.session.add_all([vehicle, customer, user])
    dbext.session.commit()
    yield dbext
