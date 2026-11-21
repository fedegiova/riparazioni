"""Repair business logic (task group 5).

Owns the validation rules that the database cannot express:
- customer/vehicle must exist in the legacy reference data (no DB FK,
  because VICLIENTI is a view and the migration must not touch
  DATIDBSTORICO),
- gas-recharge bookkeeping: a recharge decreases the cylinder's remaining
  weight in the same transaction; deleting the entry restores it.

Read-time computed fields (`total_hours`, `customer_name`) are attached to
the repair instances before serialization; they are never stored.

Every mutating function follows validate-first semantics: all checks run
(read-only) before the session is touched, so a rejected request (400/409)
never leaves partially mutated state behind. Functions do NOT commit — the
route commits, keeping related writes in one transaction.
"""

from io import BytesIO

from openpyxl import Workbook

from app.extensions import db
from app.models import (
    GAS_SYSTEM_STATES,
    Customer,
    GasCylinder,
    RepairPart,
    Repairs,
    RepairWorkLog,
    ServicePart,
    Vehicle,
)
from app.services.errors import BadRequest, Conflict, NotFound

# --- field parsing / validation (read-only) ------------------------------------

def _parse_datetime(value, name: str):
    if value in (None, ""):
        return None
    from datetime import datetime

    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise BadRequest(f"{name} must be an ISO 8601 datetime") from None
    raise BadRequest(f"{name} must be an ISO 8601 datetime")


def _parse_date(value, name: str):
    if value in (None, ""):
        return None
    from datetime import date, datetime

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise BadRequest(f"{name} must be an ISO 8601 date") from None
    raise BadRequest(f"{name} must be an ISO 8601 date")


def _validate_external_reference(model, item_id, name: str) -> None:
    """customer/vehicle have no DB FK: verify against the legacy data (409)."""
    if item_id is not None and db.session.get(model, item_id) is None:
        raise Conflict(f"{name} {item_id} does not exist")


def _validate_parts_payload(raw_parts) -> list[dict]:
    """Validate a parts payload; returns ready-to-persist dicts."""
    if raw_parts is None:
        return []
    if not isinstance(raw_parts, list):
        raise BadRequest("parts must be a list")
    parsed = []
    for raw in raw_parts:
        if not isinstance(raw, dict) or "id_part" not in raw:
            raise BadRequest("each part needs an id_part")
        part_id = raw["id_part"]
        if db.session.get(ServicePart, part_id) is None:
            raise Conflict(f"part {part_id} does not exist")
        quantity = raw.get("quantity")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            raise BadRequest(f"part {part_id} needs a positive integer quantity")
        unit_price = raw.get("unit_price")
        if unit_price is not None and (
            not isinstance(unit_price, int) or isinstance(unit_price, bool)
        ):
            raise BadRequest(f"part {part_id} unit_price must be an integer")
        parsed.append({"id_part": part_id, "quantity": quantity, "unit_price": unit_price})
    return parsed


def _validate_repair_payload(data: dict) -> None:
    """All read-only checks for create/update (external refs, parts)."""
    if "customer" in data:
        _validate_external_reference(Customer, data["customer"], "customer")
    if "vehicle" in data:
        _validate_external_reference(Vehicle, data["vehicle"], "vehicle")
    if "parts" in data:
        _validate_parts_payload(data["parts"])


# --- gas recharge validation / application --------------------------------------

def _parse_work_log_gas(data: dict) -> dict:
    state = data.get("gas_system_state")
    if state is not None and state == "":
        state = None
    return {
        "state": state,
        "cylinder": data.get("gas_recharge"),
        "weight": data.get("gas_recharge_weight"),
        "recovered": data.get("gas_recovered_weight"),
    }


def _validate_gas(entry, state, cylinder_id, weight, recovered) -> None:
    """Read-only validation of a gas dataset.

    *entry* is the existing entry being updated, or None for a new entry.

    Field matrix::

        state               cylinder   recharge        recovered
        VUOTO               required   required (>0)    forbidden
        PIENO               forbidden  forbidden       forbidden
        RECUPERO            required   forbidden       required (>=0)
        RICUPERO_RICARICA   required   required (>0)    required (>=0)
    """
    has_cylinder = cylinder_id is not None
    has_weight = weight is not None
    has_recovered = recovered is not None

    if state is not None and state not in GAS_SYSTEM_STATES:
        raise BadRequest(f"gas_system_state must be one of {', '.join(GAS_SYSTEM_STATES)}")

    # Any entry carrying gas data must declare the system state.
    if state is None:
        if has_cylinder or has_weight or has_recovered:
            raise BadRequest("an entry carrying gas data requires a gas_system_state")
        return

    # A full system stores no gas data at all.
    if state == "PIENO":
        if has_cylinder or has_weight or has_recovered:
            raise BadRequest("PIENO entries must not carry cylinder or weight data")
        return

    # Every other state moves gas through a cylinder.
    if not has_cylinder:
        raise BadRequest(f"{state} entries require a gas_recharge cylinder")

    if state in ("VUOTO", "RICUPERO_RICARICA"):
        if not has_weight:
            raise BadRequest(
                f"{state} entries require a positive gas_recharge_weight"
            )
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight <= 0:
            raise BadRequest("gas_recharge_weight must be a positive number")
    elif has_weight:  # RECUPERO
        raise BadRequest("RECUPERO entries must not carry a gas_recharge_weight")

    if state in ("RECUPERO", "RICUPERO_RICARICA"):
        if not has_recovered:
            raise BadRequest(f"{state} entries require a gas_recovered_weight")
        if (
            not isinstance(recovered, (int, float))
            or isinstance(recovered, bool)
            or recovered < 0
        ):
            raise BadRequest("gas_recovered_weight must be a non-negative number")
    elif has_recovered:  # VUOTO
        raise BadRequest("VUOTO entries must not carry a gas_recovered_weight")

    cylinder = db.session.get(GasCylinder, cylinder_id)
    if cylinder is None:
        raise Conflict(f"cylinder {cylinder_id} does not exist")

    # An update of an entry that already moved gas through this cylinder must
    # reverse the old movement before checking the new one.
    effective = cylinder.remaining_weight or 0.0
    if (
        entry is not None
        and entry.id is not None
        and entry.gas_recharge == cylinder.id
    ):
        effective += (entry.gas_recharge_weight or 0.0) - (
            entry.gas_recovered_weight or 0.0
        )

    result = effective + (recovered or 0.0) - (weight or 0.0)
    if result < 0:
        raise BadRequest(
            f"cannot recharge {weight} from cylinder {cylinder_id}: only {effective} available"
        )
    if result > cylinder.full_weight:
        raise BadRequest(
            f"recovering {recovered} would exceed cylinder {cylinder_id} "
            f"full weight {cylinder.full_weight}"
        )


def _apply_gas(entry: RepairWorkLog, state, cylinder_id, weight, recovered) -> None:
    """Apply an already-validated gas dataset (mutation only).

    A recovered weight adds to the cylinder balance and a recharged weight
    subtracts from it; the two are stored independently.
    """
    _reverse_gas(entry)
    entry.gas_system_state = state
    entry.gas_recharge = cylinder_id
    entry.gas_recharge_weight = weight if cylinder_id is not None else None
    entry.gas_recovered_weight = recovered
    if cylinder_id is not None:
        cylinder = db.session.get(GasCylinder, cylinder_id)
        cylinder.remaining_weight = (
            (cylinder.remaining_weight or 0.0)
            + (recovered or 0.0)
            - (weight or 0.0)
        )


def _reverse_gas(entry: RepairWorkLog) -> None:
    """Undo the entry's gas movement when it is updated or removed."""
    if entry.gas_recharge is None:
        return
    cylinder = db.session.get(GasCylinder, entry.gas_recharge)
    if cylinder is not None:
        cylinder.remaining_weight = (
            (cylinder.remaining_weight or 0.0)
            + (entry.gas_recharge_weight or 0.0)
            - (entry.gas_recovered_weight or 0.0)
        )


# --- read-time computed fields ----------------------------------------------------

def _duration_hours(entry: RepairWorkLog) -> float:
    """Worked hours of one entry; entries missing a bound contribute zero."""
    if entry.start_time is None or entry.end_time is None:
        return 0.0
    return (entry.end_time - entry.start_time).total_seconds() / 3600.0


def _resolve_customer_names(customer_ids: set) -> dict:
    """Look up customer names for the given ids (one query, no per-row lookup)."""
    ids = {cid for cid in customer_ids if cid is not None}
    if not ids:
        return {}
    rows = db.session.execute(
        db.select(Customer).where(Customer.ID.in_(ids))
    ).scalars()
    return {customer.ID: customer.CLIENTE for customer in rows}


def _decorate_repairs(repairs: list[Repairs]) -> None:
    """Attach computed fields to repairs before serialization.

    A single query loads the work-log durations and recharged weights of every
    listed repair (no per-repair query); customer names are resolved for the
    distinct ids in one lookup. Unknown customer ids resolve to a null name.
    """
    ids = [repair.id for repair in repairs]
    hours: dict[int, float] = {}
    gas: dict[int, float] = {}
    if ids:
        entries = db.session.execute(
            db.select(RepairWorkLog).where(RepairWorkLog.id_repairs.in_(ids))
        ).scalars()
        for entry in entries:
            hours[entry.id_repairs] = hours.get(entry.id_repairs, 0.0) + _duration_hours(entry)
            gas[entry.id_repairs] = gas.get(entry.id_repairs, 0.0) + (
                entry.gas_recharge_weight or 0.0
            )
    names = _resolve_customer_names({repair.customer for repair in repairs})
    for repair in repairs:
        repair.total_hours = hours.get(repair.id, 0.0)
        repair.gas_used = gas.get(repair.id, 0.0)
        repair.customer_name = names.get(repair.customer)


# --- repair CRUD ------------------------------------------------------------------

def _apply_repair_fields(repair: Repairs, data: dict) -> None:
    """Mutation-only; payload must already be validated."""
    if "customer" in data:
        repair.customer = data["customer"]
    if "vehicle" in data:
        repair.vehicle = data["vehicle"]
    if "refrigerator" in data:
        repair.refrigerator = data["refrigerator"]
    if "notes" in data:
        repair.notes = data["notes"]
    if "end_data" in data:
        repair.end_data = _parse_datetime(data["end_data"], "end_data")
    if "delivery_date" in data:
        repair.delivery_date = _parse_date(data["delivery_date"], "delivery_date")
    if "start_data" in data and data["start_data"] is not None:
        repair.start_data = _parse_datetime(data["start_data"], "start_data")


def create_repair(data: dict) -> Repairs:
    _validate_repair_payload(data)
    parsed_parts = _validate_parts_payload(data.get("parts"))

    repair = Repairs()  # start_data uses the model default (now)
    _apply_repair_fields(repair, data)
    db.session.add(repair)
    db.session.flush()  # assign the id so part rows can reference it
    for item in parsed_parts:
        repair.parts.append(RepairPart(id_repairs=repair.id, **item))
    _decorate_repairs([repair])
    return repair


def get_repair(item_id: int) -> Repairs:
    repair = db.session.get(Repairs, item_id)
    if repair is None:
        raise NotFound(f"repair {item_id} not found")
    _decorate_repairs([repair])
    return repair


def list_repairs(params: dict) -> list[Repairs]:
    query = db.select(Repairs).order_by(Repairs.start_data.desc(), Repairs.id.desc())
    for param, column in (
        ("customer", Repairs.customer),
        ("vehicle", Repairs.vehicle),
        ("refrigerator", Repairs.refrigerator),
    ):
        if params.get(param) not in (None, ""):
            query = query.where(column == int(params[param]))
    start_from = _parse_datetime(params.get("start_date_from"), "start_date_from")
    start_to = _parse_datetime(params.get("start_date_to"), "start_date_to")
    if start_from is not None:
        query = query.where(Repairs.start_data >= start_from)
    if start_to is not None:
        query = query.where(Repairs.start_data <= start_to)
    repairs = list(db.session.execute(query).scalars().all())
    _decorate_repairs(repairs)
    return repairs


def update_repair(repair: Repairs, data: dict) -> Repairs:
    _validate_repair_payload(data)
    parsed_parts = _validate_parts_payload(data["parts"]) if "parts" in data else None

    _apply_repair_fields(repair, data)
    if parsed_parts is not None:
        for existing in list(repair.parts):
            db.session.delete(existing)
        for item in parsed_parts:
            repair.parts.append(RepairPart(id_repairs=repair.id, **item))
    _decorate_repairs([repair])
    return repair


def delete_repair(repair: Repairs) -> None:
    """Delete a repair, reversing its gas movements on the cylinders first.

    The ORM cascade removes the work-log entries and part rows; the balance
    restore must happen before that, since each deleted entry that moved gas
    must be undone on its cylinder (same transaction).
    """
    for entry in repair.work_log:
        _reverse_gas(entry)
    db.session.delete(repair)


# --- work log ------------------------------------------------------------------------

def _apply_non_gas_fields(entry: RepairWorkLog, data: dict) -> None:
    if "start_time" in data:
        entry.start_time = _parse_datetime(data["start_time"], "start_time")
    if "end_time" in data:
        entry.end_time = _parse_datetime(data["end_time"], "end_time")
    if "operator" in data:
        entry.operator = data["operator"]


def _gas_fields_present(data: dict) -> bool:
    return any(
        key in data
        for key in (
            "gas_system_state",
            "gas_recharge",
            "gas_recharge_weight",
            "gas_recovered_weight",
        )
    )


def add_work_log_entry(repair: Repairs, data: dict) -> RepairWorkLog:
    gas = _parse_work_log_gas(data)
    _validate_gas(None, gas["state"], gas["cylinder"], gas["weight"], gas["recovered"])

    entry = RepairWorkLog(id_repairs=repair.id)
    _apply_non_gas_fields(entry, data)
    _apply_gas(
        entry,
        gas["state"],
        gas["cylinder"],
        gas["weight"],
        gas["recovered"],
    )
    db.session.add(entry)
    return entry


def get_work_log_entry(repair: Repairs, entry_id: int) -> RepairWorkLog:
    entry = db.session.get(RepairWorkLog, entry_id)
    if entry is None or entry.id_repairs != repair.id:
        raise NotFound(f"work-log entry {entry_id} not found for repair {repair.id}")
    return entry


def update_work_log_entry(entry: RepairWorkLog, data: dict) -> RepairWorkLog:
    gas = _parse_work_log_gas(data) if _gas_fields_present(data) else None
    if gas is not None:
        # Read-only validation first, against the entry's current values.
        _validate_gas(entry, gas["state"], gas["cylinder"], gas["weight"], gas["recovered"])

    _apply_non_gas_fields(entry, data)
    if gas is not None:
        _apply_gas(entry, gas["state"], gas["cylinder"], gas["weight"], gas["recovered"])
    return entry


def delete_work_log_entry(entry: RepairWorkLog) -> None:
    _reverse_gas(entry)
    db.session.delete(entry)


# --- Excel export -----------------------------------------------------------------

EXPORT_COLUMNS = (
    "id",
    "customer",
    "customer_name",
    "vehicle",
    "refrigerator",
    "start_data",
    "end_data",
    "delivery_date",
    "total_hours",
    "gas_used",
    "notes",
)


def export_repairs_xlsx(repairs: list[Repairs]) -> bytes:
    """Render repairs (already filtered and decorated) as an .xlsx workbook.

    Returns the workbook bytes; the route streams them as a download.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Repairs"
    sheet.append(list(EXPORT_COLUMNS))
    for repair in repairs:
        sheet.append(
            [
                repair.id,
                repair.customer,
                repair.customer_name,
                repair.vehicle,
                repair.refrigerator,
                repair.start_data.isoformat() if repair.start_data else None,
                repair.end_data.isoformat() if repair.end_data else None,
                repair.delivery_date.isoformat() if repair.delivery_date else None,
                repair.total_hours,
                repair.gas_used,
                repair.notes,
            ]
        )
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
