"""Dev mode (``DEV_MODE=1``): development on local SQLite, without MSSQL.

Apps under test are ``development`` apps whose config class is patched into
``app.CONFIGS`` for the test — the config module reads the environment at
import time, so the class level is the clean injection point. The class
enables ``DEV_MODE`` and points the dev databases at temporary SQLite
files; the factory then performs the full dev wiring, exactly as a real
``DEV_MODE=1 flask run`` process would.
"""

from pathlib import Path

import pytest

import app as app_module
from app import config as config_module
from app.dev_db import (
    DEV_DATABASE_PATH,
    DEV_EXTERNAL_DATABASE_PATH,
    install_dev_engine_hooks,
)

DEFAULT_DEV_FILES = ("dev.sqlite3", "dev_external.sqlite3")


def _create_dev_app(tmp_path, monkeypatch, **config_overrides):
    """Development app with dev mode on, using tmp SQLite files."""

    class DevTestConfig(config_module.DevelopmentConfig):
        DEV_MODE = True
        BASE_DIR = str(tmp_path)
        UPLOAD_DIR = str(tmp_path / "uploads")
        LOG_DIR = str(tmp_path / "log")
        DEV_DATABASE_URL = f"sqlite:///{tmp_path / 'main.sqlite'}"
        DEV_EXTERNAL_DATABASE_URL = f"sqlite:///{tmp_path / 'ext.sqlite'}"

    for key, value in config_overrides.items():
        setattr(DevTestConfig, key, value)
    monkeypatch.setitem(app_module.CONFIGS, "development", DevTestConfig)
    return app_module.create_app("development")


# --- configuration resolution ------------------------------------------------


def test_dev_mode_settings_live_on_development_config_only():
    assert isinstance(config_module.DevelopmentConfig.DEV_MODE, bool)
    assert hasattr(config_module.DevelopmentConfig, "DEV_DATABASE_URL")
    assert hasattr(config_module.DevelopmentConfig, "DEV_EXTERNAL_DATABASE_URL")
    assert hasattr(config_module.DevelopmentConfig, "DEV_SEED_SQL")
    # Base and the other environments never expose the dev-mode flag, so
    # they are unaffected even if DEV_MODE is set in the environment.
    for cls in (
        config_module.BaseConfig,
        config_module.TestingConfig,
        config_module.ProductionConfig,
    ):
        assert not hasattr(cls, "DEV_MODE"), cls.__name__


def test_dev_mode_env_var_semantics(monkeypatch):
    monkeypatch.delenv("DEV_MODE", raising=False)
    assert config_module._bool("DEV_MODE", False) is False
    monkeypatch.setenv("DEV_MODE", "")
    assert config_module._bool("DEV_MODE", False) is False
    for truthy in ("1", "true", "TRUE", "yes", "on"):
        monkeypatch.setenv("DEV_MODE", truthy)
        assert config_module._bool("DEV_MODE", False) is True, truthy
    for falsy in ("0", "false", "no", "off"):
        monkeypatch.setenv("DEV_MODE", falsy)
        assert config_module._bool("DEV_MODE", False) is False, falsy


def test_factory_leaves_database_untouched_when_dev_mode_off(tmp_path, monkeypatch):
    class DevOffConfig(config_module.DevelopmentConfig):
        DEV_MODE = False
        # Any sqlite URL keeps engine creation free of the ODBC driver.
        SQLALCHEMY_DATABASE_URI = "sqlite://"
        BASE_DIR = str(tmp_path)
        UPLOAD_DIR = str(tmp_path / "uploads")
        LOG_DIR = str(tmp_path / "log")

    monkeypatch.setitem(app_module.CONFIGS, "development", DevOffConfig)
    app = app_module.create_app("development")
    # No dev-mode side effects: URL untouched, nothing resolved.
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"
    assert DEV_DATABASE_PATH not in app.config
    assert DEV_EXTERNAL_DATABASE_PATH not in app.config


def test_dev_mode_on_resolves_sqlite_dev_databases(tmp_path, monkeypatch):
    app = _create_dev_app(tmp_path, monkeypatch)
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:")
    assert app.config["SQLALCHEMY_DATABASE_URI"] == (
        f"sqlite:///{tmp_path / 'main.sqlite'}"
    )
    assert app.config[DEV_DATABASE_PATH] == str(tmp_path / "main.sqlite")
    assert app.config[DEV_EXTERNAL_DATABASE_PATH] == str(tmp_path / "ext.sqlite")


def test_dev_mode_defaults_to_var_sqlite_files(tmp_path, monkeypatch):
    # No DEV_*_DATABASE_URL overrides: resolution must fall back to
    # <BASE_DIR>/var/dev.sqlite3 + the _external sibling.
    app = _create_dev_app(
        tmp_path,
        monkeypatch,
        DEV_DATABASE_URL=None,
        DEV_EXTERNAL_DATABASE_URL=None,
    )
    assert app.config["SQLALCHEMY_DATABASE_URI"] == (
        f"sqlite:///{tmp_path / 'var' / 'dev.sqlite3'}"
    )
    assert app.config[DEV_DATABASE_PATH] == str(tmp_path / "var" / "dev.sqlite3")
    assert app.config[DEV_EXTERNAL_DATABASE_PATH] == str(tmp_path / "var" / "dev_external.sqlite3")


# --- engine hooks: DATIDBSTORICO attach + foreign keys ------------------------


def test_dev_engine_attaches_external_schema_and_enforces_fks(tmp_path, monkeypatch):
    from app.extensions import db

    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context(), db.engine.connect() as conn:
        names = [
            row[1] for row in conn.exec_driver_sql("PRAGMA database_list").fetchall()
        ]
        assert "DATIDBSTORICO" in names
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
    # Opening a connection materialized both files.
    assert (tmp_path / "main.sqlite").exists()
    assert (tmp_path / "ext.sqlite").exists()


def test_engine_hooks_install_is_idempotent(tmp_path, monkeypatch):
    from app.extensions import db

    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context():
        # The factory already installed the hooks; a second install must
        # be a no-op (a duplicated ATTACH would error on the next connect).
        install_dev_engine_hooks(app)
        with db.engine.connect() as conn:
            names = [
                row[1] for row in conn.exec_driver_sql("PRAGMA database_list").fetchall()
            ]
    assert names.count("DATIDBSTORICO") == 1


def test_dev_databases_use_overridden_locations_not_defaults(tmp_path, monkeypatch):
    from app.extensions import db

    for name in DEFAULT_DEV_FILES:
        (config_module.PROJECT_ROOT / "var" / name).unlink(missing_ok=True)

    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context(), db.engine.connect():
        pass

    assert (tmp_path / "main.sqlite").exists()
    assert (tmp_path / "ext.sqlite").exists()
    for name in DEFAULT_DEV_FILES:
        assert not (Path(config_module.PROJECT_ROOT) / "var" / name).exists()


# --- prebaked seed data ----------------------------------------------------------


def test_prebaked_seed_rows(tmp_path, monkeypatch):
    from datetime import date

    from app.dev_db import init_dev_app
    from app.extensions import db
    from app.models import AppUser, Customer, Vehicle

    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context():
        init_dev_app(app)
        customers = db.session.execute(db.select(Customer)).scalars().all()
        vehicles = db.session.execute(db.select(Vehicle)).scalars().all()
        users = db.session.execute(db.select(AppUser)).scalars().all()

    # Exactly the prebaked rows, nothing else.
    assert len(customers) == 1
    customer = customers[0]
    assert customer.ID == 9
    assert customer.CLIENTE == "PP."
    assert customer.CITTA == "SASSUOLO"
    assert customer.CELL is None  # whitespace-only CHAR stripped to NULL

    assert len(vehicles) == 1
    vehicle = vehicles[0]
    assert vehicle.ID_INT == 12363
    assert vehicle.AUTOCARRO == "IVECO 130E18"
    assert vehicle.TARGA == "417023"
    assert vehicle.PROD == date(2003, 9, 1)  # {d '...'} rendered as ISO date

    assert len(users) == 1
    user = users[0]
    assert user.ID_INT == 21
    assert user.NAME == "LORENZA"
    assert "password" not in user.to_dict()


# --- dev-init -------------------------------------------------------------------

OWNED_TABLES = {
    "PICTURES",
    "REFRIGERATORS",
    "GAS_CYLINDERS",
    "REPAIRS",
    "SERVICE_PARTS",
    "REPAIR_PARTS",
    "REPAIR_WORK_LOG",
}
EXTERNAL_TABLES = {"TBALLESTIMENTI", "TBUSERS", "VICLIENTI"}


def _head_revision():
    from alembic.script import ScriptDirectory

    from app.dev_db import _alembic_config

    return ScriptDirectory.from_config(_alembic_config()).get_heads()[0]


def _version(engine):
    return engine.connect().exec_driver_sql(
        "SELECT version_num FROM alembic_version"
    ).scalar()


def test_first_init_creates_and_seeds(tmp_path, monkeypatch):
    from sqlalchemy import inspect as sa_inspect

    from app.dev_db import init_dev_app
    from app.extensions import db
    from app.models import Customer, Repairs

    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context():
        init_dev_app(app)

        inspector = sa_inspect(db.engine)
        assert OWNED_TABLES <= set(inspector.get_table_names())
        assert set(inspector.get_table_names(schema="DATIDBSTORICO")) == EXTERNAL_TABLES
        assert _version(db.engine) == _head_revision()

        # Seeded rows present, owned tables empty.
        assert db.session.execute(db.select(Customer)).scalars().first().ID == 9
        assert db.session.execute(db.select(Repairs)).scalars().all() == []


def test_reinit_is_noop_after_api_rows(tmp_path, monkeypatch):
    from app.dev_db import init_dev_app
    from app.extensions import db
    from app.models import Customer, Refrigerator, Vehicle

    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context():
        init_dev_app(app)
        db.session.add(Refrigerator(brand="KEPT"))
        db.session.commit()

        init_dev_app(app)  # second run on a populated dev database

        # API-created rows untouched, no duplicate seed rows.
        assert [r.brand for r in db.session.execute(db.select(Refrigerator)).scalars()] == [
            "KEPT"
        ]
        assert len(db.session.execute(db.select(Customer)).scalars().all()) == 1
        assert len(db.session.execute(db.select(Vehicle)).scalars().all()) == 1


def test_reset_wipes_owned_and_reseeds_external(tmp_path, monkeypatch):
    from app.dev_db import init_dev_app
    from app.extensions import db
    from app.models import Customer, Refrigerator

    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context():
        init_dev_app(app)
        db.session.add(Refrigerator(brand="DOOMED"))
        db.session.commit()

        init_dev_app(app, reset=True)

        # Owned tables empty again, at head.
        assert db.session.execute(db.select(Refrigerator)).scalars().all() == []
        assert _version(db.engine) == _head_revision()
        # External tables hold exactly the prebaked seed rows again.
        assert [c.ID for c in db.session.execute(db.select(Customer)).scalars()] == [9]


def test_reset_on_fresh_environment_initializes(tmp_path, monkeypatch):
    from sqlalchemy import inspect as sa_inspect

    from app.dev_db import init_dev_app
    from app.extensions import db
    from app.models import Customer

    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context():
        init_dev_app(app, reset=True)

        assert OWNED_TABLES <= set(sa_inspect(db.engine).get_table_names())
        assert (
            set(sa_inspect(db.engine).get_table_names(schema="DATIDBSTORICO"))
            == EXTERNAL_TABLES
        )
        assert _version(db.engine) == _head_revision()
        assert db.session.execute(db.select(Customer)).scalars().first().ID == 9


def test_reset_with_custom_seed_replaces_prebaked(tmp_path, monkeypatch):
    from app.dev_db import init_dev_app
    from app.extensions import db
    from app.models import AppUser, Customer, Vehicle

    custom = tmp_path / "custom_seed.sql"
    custom.write_text(
        "INSERT INTO DATIDBSTORICO.VICLIENTI (ID, N_NOMINATIVO, CLIENTE)\n"
        "VALUES (1, 1, 'ACME'), (2, 2, 'BETA');\n",
        encoding="utf-8",
    )
    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context():
        init_dev_app(app)
        assert len(db.session.execute(db.select(Customer)).scalars().all()) == 1

        init_dev_app(app, reset=True, seed_path=str(custom))

        assert [c.CLIENTE for c in db.session.execute(db.select(Customer)).scalars()] == [
            "ACME",
            "BETA",
        ]
        # Tables without custom seed rows are empty after the reset.
        assert db.session.execute(db.select(Vehicle)).scalars().all() == []
        assert db.session.execute(db.select(AppUser)).scalars().all() == []


def test_missing_seed_file_is_a_hard_error(tmp_path, monkeypatch):
    from app.dev_db import init_dev_app

    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context():
        missing = tmp_path / "does_not_exist.sql"
        with pytest.raises(RuntimeError, match=str(missing)):
            init_dev_app(app, seed_path=str(missing))


# --- end-to-end API transparency ------------------------------------------------


def _initialized_dev_client(tmp_path, monkeypatch):
    from app.dev_db import init_dev_app

    app = _create_dev_app(tmp_path, monkeypatch)
    with app.app_context():
        init_dev_app(app)
    return app.test_client()


def test_dev_mode_health_and_reference_reads(tmp_path, monkeypatch):
    client = _initialized_dev_client(tmp_path, monkeypatch)

    assert client.get("/healthz").status_code == 200
    db_health = client.get("/healthz/db")
    assert db_health.status_code == 200
    assert db_health.get_json()["database"] == "reachable"

    # Seeded rows served in the production response shape.
    vehicles = client.get("/api/v1/vehicles").get_json()
    assert len(vehicles) == 1
    assert vehicles[0]["id"] == 12363
    assert vehicles[0]["autocarro"] == "IVECO 130E18"

    customers = client.get("/api/v1/customers").get_json()
    assert len(customers) == 1
    assert customers[0]["id"] == 9
    assert customers[0]["cliente"] == "PP."

    users = client.get("/api/v1/users").get_json()
    assert len(users) == 1
    assert users[0]["id"] == 21
    assert "password" not in users[0]


def test_dev_mode_repairs_against_seeded_reference_data(tmp_path, monkeypatch):
    client = _initialized_dev_client(tmp_path, monkeypatch)

    created = client.post(
        "/api/v1/repairs",
        json={"type": "RIPA", "customer": 9, "vehicle": 12363},
    )
    assert created.status_code == 201
    assert created.get_json()["customer"] == 9
    assert created.get_json()["vehicle"] == 12363

    rejected = client.post(
        "/api/v1/repairs", json={"type": "RIPA", "customer": 999}
    )
    assert rejected.status_code == 409


def test_dev_mode_error_semantics_unchanged(tmp_path, monkeypatch):
    client = _initialized_dev_client(tmp_path, monkeypatch)

    # Writes to read-only reference data: 405.
    assert client.post("/api/v1/customers", json={"cliente": "X"}).status_code == 405

    # FK enforcement: a refrigerator referenced by a repair cannot be deleted.
    fridge = client.post(
        "/api/v1/refrigerators", json={"brand": "BRAVO", "model": "M1"}
    )
    assert fridge.status_code == 201
    fridge_id = fridge.get_json()["id"]
    repair = client.post(
        "/api/v1/repairs",
        json={"type": "RIPA", "customer": 9, "refrigerator": fridge_id},
    )
    assert repair.status_code == 201

    assert client.delete(f"/api/v1/refrigerators/{fridge_id}").status_code == 409
