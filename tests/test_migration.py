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
    "TRANSACTION_GUARDS",
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
        assert "archived_total_hours" in columns, columns
        assert "type" not in columns, columns

        work_log_columns = {
            column["name"] for column in inspector.get_columns("REPAIR_WORK_LOG")
        }
        assert "description" in work_log_columns, work_log_columns

        # Schema delta: the new work-log gas-operation columns.
        assert {"gas_operation", "gas_measured_kg", "gas_nameplate_kg"} <= (
            work_log_columns
        ), work_log_columns

        # Refrigerator installation link, gas type, and the per-allestimento
        # uniqueness of installed units.
        refrigerator_columns = {
            column["name"]: column
            for column in inspector.get_columns("REFRIGERATORS")
        }
        assert {"allestimento_id", "gas_kind"} <= set(refrigerator_columns), (
            refrigerator_columns
        )
        assert refrigerator_columns["allestimento_id"]["nullable"] is True
        allestimento_indexes = {
            index["name"]: index
            for index in inspector.get_indexes("REFRIGERATORS")
        }
        assert "uq_refrigerators_allestimento" in allestimento_indexes, (
            allestimento_indexes
        )
        assert bool(allestimento_indexes["uq_refrigerators_allestimento"]["unique"])

        # Repair gas-equipment lock, defaulting to false and not nullable.
        repair_columns = {
            column["name"]: column
            for column in inspector.get_columns("REPAIRS")
        }
        assert "gas_equipment_locked" in repair_columns, repair_columns
        assert repair_columns["gas_equipment_locked"]["nullable"] is False

        guard_rows = db.session.execute(
            sa.text("SELECT id, version FROM TRANSACTION_GUARDS")
        ).all()
        assert guard_rows == [(1, 0)]

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


def test_archived_totals_are_backfilled_with_the_old_elapsed_sum(tmp_path):
    """Repairs archived before rollout keep the totals they reported."""
    db_path = tmp_path / "backfill.sqlite"
    app = _create_test_app(tmp_path)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    with app.app_context():
        from app.extensions import db

        cfg = Config(str(PROJECT_ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
        command.upgrade(cfg, "a3f1c7e29b04")

        repairs = sa.table(
            "REPAIRS",
            sa.column("id", sa.Integer),
            sa.column("customer", sa.Integer),
            sa.column("vehicle", sa.Integer),
            sa.column("end_data", sa.DateTime),
        )
        logs = sa.table(
            "REPAIR_WORK_LOG",
            sa.column("id", sa.Integer),
            sa.column("id_repairs", sa.Integer),
            sa.column("start_time", sa.DateTime),
            sa.column("end_time", sa.DateTime),
            sa.column("operator", sa.String),
        )
        from datetime import datetime

        with db.engine.begin() as conn:
            conn.execute(
                sa.insert(repairs),
                [
                    {
                        "id": 1,
                        "customer": 1,
                        "vehicle": 1,
                        "end_data": datetime(2026, 1, 2, 10, 0),
                    },
                    {"id": 2, "customer": 1, "vehicle": 1, "end_data": None},
                ],
            )
            conn.execute(
                sa.insert(logs),
                [
                    {
                        "id": 1,
                        "id_repairs": 1,
                        "start_time": datetime(2026, 1, 1, 8, 0),
                        "end_time": datetime(2026, 1, 1, 9, 30),
                        "operator": "FABRI",
                    },
                    {
                        "id": 2,
                        "id_repairs": 1,
                        "start_time": datetime(2026, 1, 1, 10, 0),
                        "end_time": datetime(2026, 1, 1, 12, 0),
                        "operator": "FABRI",
                    },
                    {
                        "id": 3,
                        "id_repairs": 1,
                        "start_time": datetime(2026, 1, 1, 13, 0),
                        "end_time": None,
                        "operator": "FABRI",
                    },
                    {
                        "id": 4,
                        "id_repairs": 2,
                        "start_time": datetime(2026, 1, 1, 8, 0),
                        "end_time": datetime(2026, 1, 1, 9, 0),
                        "operator": "FABRI",
                    },
                ],
            )

        command.upgrade(cfg, "head")

        rows = dict(
            db.session.execute(
                sa.text("SELECT id, archived_total_hours FROM REPAIRS")
            ).all()
        )
        assert rows[1] == 3.5  # 1h30 + 2h00; the open entry contributes zero
        assert rows[2] is None  # active repairs stay live

        # Existing work logs are untouched: no description was invented.
        descriptions = db.session.execute(
            sa.text("SELECT description FROM REPAIR_WORK_LOG")
        ).scalars().all()
        assert descriptions == [None, None, None, None]


def test_upgrade_does_not_require_obsolete_gas_columns(tmp_path):
    """The new migration must succeed even where the old gas columns are gone.

    The deployed schema is not guaranteed to carry the pre-change state/weight
    columns, so the upgrade only adds new columns and never touches them.
    """
    db_path = tmp_path / "obsolete.sqlite"
    app = _create_test_app(tmp_path)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    with app.app_context():
        from app.extensions import db

        cfg = Config(str(PROJECT_ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
        command.upgrade(cfg, "b2c4d6e8f0a1")

        with db.engine.begin() as conn:
            for column in (
                "gas_system_state",
                "gas_recharge_weight",
                "gas_recovered_weight",
            ):
                conn.execute(sa.text(f"ALTER TABLE REPAIR_WORK_LOG DROP COLUMN {column}"))

        # Must not fail on the missing legacy columns.
        command.upgrade(cfg, "head")

        columns = {
            column["name"]
            for column in sa.inspect(db.engine).get_columns("REPAIR_WORK_LOG")
        }
        assert {"gas_operation", "gas_measured_kg", "gas_nameplate_kg"} <= columns
        assert "gas_system_state" not in columns


def test_allestimento_index_compiles_for_sql_server():
    """The installation uniqueness renders as a filtered index on MSSQL."""
    from sqlalchemy.dialects import mssql
    from sqlalchemy.schema import CreateIndex

    from app.models import Refrigerator

    index = next(
        index
        for index in Refrigerator.__table__.indexes
        if index.name == "uq_refrigerators_allestimento"
    )
    ddl = str(CreateIndex(index).compile(dialect=mssql.dialect()))
    assert "UNIQUE" in ddl.upper()
    assert "WHERE allestimento_id IS NOT NULL" in ddl
