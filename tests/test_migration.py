"""Migration round-trip test (task 1.4).

Runs the real Alembic migration suite against a temporary SQLite file
database (Alembic opens its own connections, so an in-memory database is
not usable here) and verifies:
- ``upgrade head`` creates every owned table,
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
    "REFILLS",
    "REPAIRS",
    "SERVICE_PARTS",
    "REPAIR_PARTS",
    "REPAIR_WORK_LOG",
    "SETTINGS",
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

        # Schema delta: delivery_date replaces the removed type column.
        columns = {column["name"] for column in inspector.get_columns("REPAIRS")}
        assert "delivery_date" in columns, columns
        assert "type" not in columns, columns

        # Schema delta: cylinders gain the archive flag and a required weight.
        cylinder_columns = {
            column["name"]: column
            for column in inspector.get_columns("GAS_CYLINDERS")
        }
        assert "archived" in cylinder_columns, cylinder_columns
        assert cylinder_columns["archived"]["nullable"] is False
        assert cylinder_columns["full_weight"]["nullable"] is False

        # Schema delta: PICTURES carries an owner pair; the single picture_ref
        # link is gone from the owned tables.
        picture_columns = {
            column["name"]: column
            for column in inspector.get_columns("PICTURES")
        }
        assert {"owner_type", "owner_id"} <= set(picture_columns), picture_columns
        assert picture_columns["owner_type"]["nullable"] is False
        assert picture_columns["owner_id"]["nullable"] is False
        for table in ("GAS_CYLINDERS", "SERVICE_PARTS"):
            columns = {c["name"] for c in inspector.get_columns(table)}
            assert "picture_ref" not in columns, (table, columns)

        # Rolling back one revision restores the pre-change shape.
        command.downgrade(cfg, "051870300b7a")
        inspector = sa.inspect(db.engine)
        columns = {column["name"] for column in inspector.get_columns("REPAIRS")}
        assert "type" in columns, columns
        assert "delivery_date" not in columns, columns

        command.downgrade(cfg, "base")

        inspector = sa.inspect(db.engine)
        tables = set(inspector.get_table_names())
        assert not (tables & OWNED_TABLES), f"tables still present: {tables & OWNED_TABLES}"
