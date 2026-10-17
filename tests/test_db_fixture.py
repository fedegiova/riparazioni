"""DB fixture sanity test (task 1.3).

Verifies the in-memory SQLite + attached DATIDBSTORICO setup: owned and
external tables both exist, seeded reference rows are readable, and a
repair whose FKs point at the seeded external rows persists.
"""

from sqlalchemy.exc import IntegrityError

from app.models import Customer, GasCylinder, Repairs, Vehicle


def test_external_seed_rows_readable(db):
    vehicle = db.session.get(Vehicle, 1)
    customer = db.session.get(Customer, 1)
    assert vehicle.TARGA == "ABC123"
    assert customer.CLIENTE == "ACME SRL"


def test_repair_with_valid_external_fk_persists(db):
    repair = Repairs(customer=1, vehicle=1, type="RIPA")
    db.session.add(repair)
    db.session.commit()
    assert repair.id is not None
    assert repair.start_data is not None


def test_work_log_fk_to_owned_cylinder_enforced(db):
    """FKs between owned tables ARE enforced at the DB level (same database)."""
    from app.models import RepairWorkLog

    entry = RepairWorkLog(id_repairs=99999, operator="X")
    db.session.add(entry)
    try:
        db.session.commit()
        raise AssertionError("expected IntegrityError for unknown repair id")
    except IntegrityError:
        db.session.rollback()


def test_gas_cylinder_balance_fields(db):
    cylinder = GasCylinder(gas_kind="R134a", full_weight=10.0, remaining_weight=10.0)
    db.session.add(cylinder)
    db.session.commit()
    assert cylinder.remaining_weight == 10.0
