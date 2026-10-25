"""Dev-mode database support: run the backend on local SQLite, not MSSQL.

When ``DEV_MODE`` is enabled in the development configuration the app runs
against two local SQLite files under the runtime directory:

- the **primary** database holding the owned (migrated) tables, and
- a second file that is ``ATTACH``ed as the ``DATIDBSTORICO`` schema on
  every connection, so the read-only legacy objects (vehicles, customers,
  users) resolve exactly as they do against MSSQL — the same pattern the
  test suite uses in ``tests/conftest.py``, file-backed.

Wiring happens in two phases around ``db.init_app`` (Flask-SQLAlchemy
creates the engine eagerly there, from the config at that moment):

1. :func:`setup_dev_mode` — before ``db.init_app``: points the config at
   the dev databases and the SQLite engine options.
2. :func:`install_dev_engine_hooks` — after ``db.init_app``: ``ATTACH``es
   the ``DATIDBSTORICO`` database and enables foreign keys on every new
   connection (idempotent per engine).

Nothing runs at request time. All DDL and seeding happen through the
explicit ``flask dev-init`` command (:func:`init_dev_app`). See the README
section "Development without MSSQL (dev mode)".
"""

from pathlib import Path

import click
from flask import current_app
from sqlalchemy import event
from sqlalchemy.engine import make_url

from app import config as config_module
from app.extensions import db

# Config keys holding the resolved dev database locations (filled by
# setup_dev_mode, consumed by init_dev_app and the CLI).
DEV_DATABASE_PATH = "DEV_DATABASE_PATH"
DEV_EXTERNAL_DATABASE_PATH = "DEV_EXTERNAL_DATABASE_PATH"

# Marker attribute on the Engine so the connect hooks are installed at most
# once per engine (setup can be called repeatedly, e.g. by tests).
_HOOKS_INSTALLED = "_riparazioni_dev_hooks_installed"


def _url_path(url: str) -> Path:
    """Filesystem path of a ``sqlite:`` URL (empty path when in-memory)."""
    return Path(make_url(url).database or "")


def _default_primary_url(base_dir: Path) -> str:
    return f"sqlite:///{base_dir / 'var' / 'dev.sqlite3'}"


def _sibling_external_path(primary_path: Path) -> Path:
    """Sibling of *primary_path* with an ``_external`` suffix.

    ``var/dev.sqlite3`` -> ``var/dev_external.sqlite3``.
    """
    name = primary_path.name or "dev.sqlite3"
    stem, dot, suffix = name.rpartition(".")
    if not stem:  # name without a suffix
        stem, suffix = name, ""
    else:
        suffix = dot + suffix
    return primary_path.with_name(f"{stem}_external{suffix}")


def resolve_dev_databases(app) -> tuple[Path, Path]:
    """Resolve the primary and external dev database file paths.

    The primary file comes from ``DEV_DATABASE_URL`` (a full ``sqlite:``
    URL) or defaults to ``<BASE_DIR>/var/dev.sqlite3``. The external file
    comes from ``DEV_EXTERNAL_DATABASE_URL`` or defaults to the sibling of
    the primary file with an ``_external`` suffix.
    """
    primary_url = app.config.get("DEV_DATABASE_URL") or _default_primary_url(
        Path(app.config["BASE_DIR"])
    )
    primary_path = _url_path(primary_url)
    if app.config.get("DEV_EXTERNAL_DATABASE_URL"):
        external_path = _url_path(app.config["DEV_EXTERNAL_DATABASE_URL"])
    else:
        external_path = _sibling_external_path(primary_path)
    return primary_path, external_path


def setup_dev_mode(app) -> None:
    """Phase 1: point the app config at the local dev SQLite databases.

    Must run BEFORE ``db.init_app`` (the engine is created there, eagerly,
    from ``SQLALCHEMY_DATABASE_URI`` / ``SQLALCHEMY_ENGINE_OPTIONS``). No
    app context or engine access needed.
    """
    primary_path, external_path = resolve_dev_databases(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{primary_path}"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        # The Flask dev server is multithreaded; pooled SQLite connections
        # may be used on a different thread than the one that opened them
        # (same option tests/conftest.py uses).
        "connect_args": {"check_same_thread": False},
    }
    app.config[DEV_DATABASE_PATH] = str(primary_path)
    app.config[DEV_EXTERNAL_DATABASE_PATH] = str(external_path)


def install_dev_engine_hooks(app) -> None:
    """Phase 2: attach the external database and enable FKs per connection.

    Must run AFTER ``db.init_app`` (the engine must exist) and inside an
    app context. Idempotent: a second call on the same engine is a no-op,
    so a duplicate ``ATTACH`` can never fire on one connection.
    """
    engine = db.engine
    if getattr(engine, _HOOKS_INSTALLED, False):
        return
    external_path = Path(app.config[DEV_EXTERNAL_DATABASE_PATH])
    # ATTACH takes no bound parameters: embed the path, doubling quotes.
    attach_sql = (
        "ATTACH DATABASE "
        f"'{external_path.as_posix().replace(chr(39), chr(39) * 2)}' "
        "AS DATIDBSTORICO"
    )

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection, connection_record):
        dbapi_connection.execute(attach_sql)
        # Per-connection pragma: owned-table FKs behave as in production.
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    setattr(engine, _HOOKS_INSTALLED, True)


def require_dev_mode(app) -> None:
    """Raise with guidance when dev-init runs outside an enabled dev mode."""
    if not app.config.get("DEV_MODE") or DEV_DATABASE_PATH not in app.config:
        raise RuntimeError(
            "dev-init requires dev mode: set DEV_MODE=1 (e.g. `make dev-init`)"
        )


def init_dev_app(app, reset: bool = False, seed_path: str | None = None) -> None:
    """Prepare the dev databases (idempotent; ``reset`` wipes first).

    Must run inside an app context of a dev-mode app (the ``dev-init`` CLI
    command and the tests both do). Steps:

    1. owned tables: Alembic ``downgrade base`` (only on reset) then
       ``upgrade head`` — the real migration path, owned tables only
       (the ``include_object`` filter in ``migrations/env.py`` keeps it
       away from ``DATIDBSTORICO``);
    2. external tables: ``DROP TABLE IF EXISTS`` (only on reset) then
       ``create_all`` from the models with ``checkfirst=True`` — the DDL
       renders as ``CREATE TABLE "DATIDBSTORICO".<name>`` against the
       attached file and stays in sync with ``app/models/external.py``;
    3. seed: execute the seed SQL file when ``reset`` or when all three
       external tables are empty — a plain re-run never touches existing
       data.

    Seed source resolution: *seed_path* -> ``DEV_SEED_SQL`` -> the
    committed ``dev/seed_external.sql``. A missing file is a hard error.
    """
    from sqlalchemy import inspect

    from app import models  # noqa: F401  (register tables on the metadata)
    from app.models.external import _customer_table, _user_table, _vehicle_table

    require_dev_mode(app)
    _ensure_dev_context()

    primary_path = Path(app.config[DEV_DATABASE_PATH])
    external_path = Path(app.config[DEV_EXTERNAL_DATABASE_PATH])
    for path in (primary_path, external_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    external_tables = [_customer_table, _vehicle_table, _user_table]

    seed_source = (
        seed_path
        or app.config.get("DEV_SEED_SQL")
        or str(config_module.PROJECT_ROOT / "dev" / "seed_external.sql")
    )
    seed_file = Path(seed_source)
    if not seed_file.is_file():
        raise RuntimeError(f"dev seed file not found: {seed_file}")
    seed_sql = seed_file.read_text(encoding="utf-8")

    engine = db.engine
    migration_state = _migrate(engine, reset=reset)

    with engine.begin() as conn:
        if reset:
            for table in external_tables:
                conn.exec_driver_sql(f'DROP TABLE IF EXISTS "DATIDBSTORICO".{table.name}')
        inspector = inspect(conn)
        created = [t for t in external_tables if not inspector.has_table(t.name, schema="DATIDBSTORICO")]
        db.metadata.create_all(conn, tables=external_tables, checkfirst=True)

    seeded = "skipped (tables not empty)"
    if reset or _external_tables_empty(engine, external_tables):
        with engine.connect() as conn:
            # pysqlite executescript: issues a COMMIT, then runs the whole
            # multi-statement script (SQLAlchemy 2.0 Connection has no
            # executescript of its own).
            conn.connection.dbapi_connection.executescript(seed_sql)
        seeded = "reapplied" if reset else f"applied from {seed_file}"

    created_names = ", ".join(t.name for t in created) if created else "present"
    print(
        f"dev-init: primary={primary_path} external={external_path} | "
        f"migrations={migration_state} external={created_names} seed={seeded}"
    )


def _ensure_dev_context() -> None:
    """dev-init only makes sense for a sqlite (dev) engine."""
    if db.engine.url.get_backend_name() != "sqlite":
        raise RuntimeError(
            "dev-init requires the dev SQLite databases; the current engine "
            f"uses {db.engine.url.get_backend_name()!r}"
        )


def _alembic_config():
    from alembic.config import Config as AlembicConfig

    migrations_dir = config_module.PROJECT_ROOT / "migrations"
    cfg = AlembicConfig(str(migrations_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(migrations_dir))
    return cfg


def _current_revision(engine) -> str | None:
    from sqlalchemy import inspect

    if not inspect(engine).has_table("alembic_version"):
        return None
    with engine.connect() as conn:
        row = conn.exec_driver_sql("SELECT version_num FROM alembic_version").fetchall()
    return row[0][0] if row else None


def _migrate(engine, reset: bool) -> str:
    """Run the real Alembic migrations for the owned tables."""
    from alembic import command as alembic_command
    from alembic.script import ScriptDirectory

    cfg = _alembic_config()
    before = _current_revision(engine)
    if reset:
        alembic_command.downgrade(cfg, "base")
    alembic_command.upgrade(cfg, "head")
    head = ScriptDirectory.from_config(cfg).get_heads()[0]
    after = _current_revision(engine)
    if after != head:
        raise RuntimeError(f"migration did not reach head: {after!r} != {head!r}")
    if reset:
        return "recreated"
    if before is None:
        return "created"
    if before == head:
        return "up-to-date"
    return "upgraded"


def _external_tables_empty(engine, tables) -> bool:
    with engine.connect() as conn:
        return all(
            conn.exec_driver_sql(f'SELECT COUNT(*) FROM "DATIDBSTORICO".{t.name}').scalar() == 0
            for t in tables
        )


# --- flask CLI ------------------------------------------------------------------

@click.command("dev-init")
@click.option("--reset", is_flag=True, help="wipe all dev data, then recreate and reseed")
@click.option(
    "--seed",
    "seed_path",
    default=None,
    type=click.Path(),
    help="path to a custom seed SQL file (overrides DEV_SEED_SQL and the prebaked seed)",
)
def dev_init_command(reset: bool, seed_path: str | None) -> None:
    """Prepare the local dev databases (migrations + external tables + seed)."""
    try:
        init_dev_app(current_app, reset=reset, seed_path=seed_path)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
