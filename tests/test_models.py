"""Model and registry tests (task group 1)."""

from app.models import (
    GAS_SYSTEM_STATES,
    AppUser,
    Customer,
    GasCylinder,
    Picture,
    Refill,
    Refrigerator,
    RepairPart,
    Repairs,
    RepairWorkLog,
    ServicePart,
    Settings,
    TransactionGuard,
    Vehicle,
)


def test_owned_models_are_registered(app):
    """All owned mapped classes are registered (task 1.1)."""
    expected_tables = {
        Repairs: "REPAIRS",
        RepairWorkLog: "REPAIR_WORK_LOG",
        RepairPart: "REPAIR_PARTS",
        Refrigerator: "REFRIGERATORS",
        GasCylinder: "GAS_CYLINDERS",
        Refill: "REFILLS",
        ServicePart: "SERVICE_PARTS",
        Picture: "PICTURES",
        Settings: "SETTINGS",
        TransactionGuard: "TRANSACTION_GUARDS",
    }
    for model, table_name in expected_tables.items():
        assert model.__tablename__ == table_name, model
        assert model.__table__.schema is None, (
            f"{table_name} must live in the default schema (it is migrated)"
        )


def test_gas_cylinder_lifecycle_fields(app):
    """Cylinders carry an archived flag and a required full weight (task 1.1)."""
    columns = {c.name: c for c in GasCylinder.__table__.columns}
    assert "archived" in columns
    assert columns["archived"].nullable is False
    assert columns["full_weight"].nullable is False
    assert "RECUPERO" in GAS_SYSTEM_STATES
    assert "RICUPERO_RICARICA" in GAS_SYSTEM_STATES


def test_refill_columns(app):
    """Refills store the cylinder, date and reference (task 1.1)."""
    columns = {c.name for c in Refill.__table__.columns}
    assert {"id", "gas_cylinder_id", "date", "reference"} <= columns
    fks = list(Refill.__table__.columns["gas_cylinder_id"].foreign_keys)
    assert fks and fks[0].column.table.name == "GAS_CYLINDERS"


def test_picture_owner_columns(app):
    """Pictures carry an owner pair and no legacy picture_ref (task 1.1)."""
    columns = {c.name: c for c in Picture.__table__.columns}
    assert {"owner_type", "owner_id"} <= set(columns)
    assert columns["owner_type"].nullable is False
    assert columns["owner_id"].nullable is False
    assert columns["path"].unique is True
    assert "picture_ref" not in {c.name for c in GasCylinder.__table__.columns}
    assert "picture_ref" not in {c.name for c in ServicePart.__table__.columns}


def test_external_models_map_legacy_tables(app):
    """External models map DATIDBSTORICO tables with the documented columns (task 1.2)."""
    vehicle_cols = {c.name for c in Vehicle.__table__.columns}
    assert {"ID_INT", "ID", "NOMINATIVO_ID", "TARGA", "AUTOCARRO", "CARROZZERIA"} <= vehicle_cols
    assert Vehicle.__table__.name == "TBALLESTIMENTI"
    assert Vehicle.__table__.schema == "DATIDBSTORICO"

    customer_cols = {c.name for c in Customer.__table__.columns}
    assert {"ID", "CLIENTE", "VIA", "CAP", "CITTA", "TEL", "CELL", "EMAIL"} <= customer_cols
    assert Customer.__table__.name == "VICLIENTI"
    assert Customer.__table__.schema == "DATIDBSTORICO"

    user_cols = {c.name for c in AppUser.__table__.columns}
    assert {"ID_INT", "NAME", "PASSWORD", "LAST_LOGIN"} <= user_cols
    assert AppUser.__table__.name == "TBUSERS"
    assert AppUser.__table__.schema == "DATIDBSTORICO"


def test_app_user_serializer_never_exposes_password(app):
    user = AppUser(ID_INT=1, ID="000000000000001", NAME="Test User", PASSWORD="secret")
    data = user.to_dict()
    assert "password" not in {key.lower() for key in data}
    assert data["name"] == "Test User"
