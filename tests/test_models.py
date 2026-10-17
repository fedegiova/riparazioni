"""Model and registry tests (task group 1)."""

from app.models import (
    AppUser,
    Customer,
    GasCylinder,
    Picture,
    Refrigerator,
    RepairPart,
    Repairs,
    RepairWorkLog,
    ServicePart,
    Vehicle,
)


def test_owned_models_are_registered(app):
    """All seven owned mapped classes are registered (task 1.1)."""
    expected_tables = {
        Repairs: "REPAIRS",
        RepairWorkLog: "REPAIR_WORK_LOG",
        RepairPart: "REPAIR_PARTS",
        Refrigerator: "REFRIGERATORS",
        GasCylinder: "GAS_CYLINDERS",
        ServicePart: "SERVICE_PARTS",
        Picture: "PICTURES",
    }
    for model, table_name in expected_tables.items():
        assert model.__tablename__ == table_name, model
        assert model.__table__.schema is None, (
            f"{table_name} must live in the default schema (it is migrated)"
        )


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
