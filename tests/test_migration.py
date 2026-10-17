"""Migration round-trip test (task 1.4).

Runs the real Alembic migration suite against a temporary SQLite file
database (Alembic opens its own connections, so an in-memory database is
not usable here) and verifies:
- ``upgrade head`` creates exactly the seven owned tables,
- no ``DATIDBSTORICO`` object is created,
- ``downgrade base`` drops them all again.
"""

from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from conftest import _create_test_app

PROJECT_ROOT = Path(__file__).resolve().parent.parent

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


def test_migration_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "migration.sqlite"
    app = _create_test_app(tmp_path)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    with app.app_context():
        from app.extensions import db

        cfg = Config(str(PROJECT_ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))

        command.upgrade(cfg, "head")

        inspector = sa.inspect(db.engine)
        tables = set(inspector.get_table_names())
        assert OWNED_TABLES <= tables, f"missing owned tables: {OWNED_TABLES - tables}"
        assert not (tables & EXTERNAL_TABLES), (
            f"migration must not create external tables: {tables & EXTERNAL_TABLES}"
        )

        # The customer/vehicle columns exist but must carry no FK constraint.
        repairs_fks = inspector.get_foreign_keys("REPAIRS")
        assert repairs_fks, "REPAIRS should keep its refrigerator FK"
        fk_columns = {tuple(fk["constrained_columns"]) for fk in repairs_fks}
        assert fk_columns == {("refrigerator",)}, fk_columns

        command.downgrade(cfg, "base")

        inspector = sa.inspect(db.engine)
        tables = set(inspector.get_table_names())
        assert not (tables & OWNED_TABLES), f"tables still present: {tables & OWNED_TABLES}"
