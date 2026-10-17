"""Repair business logic (task group 5).

Owns the validation rules that the database cannot express:
- repair type must be RIPA or RIPA_FRIGO,
- customer/vehicle must exist in the legacy reference data (no DB FK,
  because VICLIENTI is a view and the migration must not touch
  DATIDBSTORICO),
- gas-recharge bookkeeping: a recharge decreases the cylinder's remaining
  weight in the same transaction; deleting the entry restores it.

Every mutating function follows validate-first semantics: all checks run
(read-only) before the session is touched, so a rejected request (400/409)
never leaves partially mutated state behind. Functions do NOT commit — the
route commits, keeping related writes in one transaction.
"""

from app.extensions import db
from app.models import (
    GAS_SYSTEM_STATES,
    REPAIR_TYPES,
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


def _validate_type(value) -> str:
    if value not in REPAIR_TYPES:
        raise BadRequest(f"type must be one of {', '.join(REPAIR_TYPES)}, got {value!r}")
    return value


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
    """All read-only checks for create/update (type, external refs, parts)."""
    if "type" in data and data["type"] is not None:
        _validate_type(data["type"])
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


def _validate_gas(repair: Repairs, entry, state, cylinder_id, weight, recovered) -> None:
    """Read-only validation of a gas dataset.

    *entry* is the existing entry being updated, or None for a new one.
    """
    has_cylinder = cylinder_id is not None
    has_weight = weight is not None

    if has_cylinder != has_weight:
        raise BadRequest(
            "a gas recharge needs both gas_recharge (cylinder) and gas_recharge_weight"
        )

    if state is not None and state not in GAS_SYSTEM_STATES:
        raise BadRequest(f"gas_system_state must be one of {', '.join(GAS_SYSTEM_STATES)}")

    # A full system stores no gas data at all.
    if state == "PIENO" and (has_cylinder or has_weight or recovered is not None):
        raise BadRequest("PIENO entries must not carry cylinder or weight data")

    if repair.type == "RIPA_FRIGO" and state is None and (
        has_cylinder or recovered is not None
    ):
        raise BadRequest("RIPA_FRIGO entries with gas data require a gas_system_state")

    if not has_cylinder:
        return

    if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight <= 0:
        raise BadRequest("gas_recharge_weight must be a positive number")
    if recovered is not None and (
        not isinstance(recovered, (int, float)) or isinstance(recovered, bool) or recovered < 0
    ):
        raise BadRequest("gas_recovered_weight must be a non-negative number")

    cylinder = db.session.get(GasCylinder, cylinder_id)
    if cylinder is None:
        raise Conflict(f"cylinder {cylinder_id} does not exist")

    # An update of an entry that already draws from this cylinder must count
    # the old draw back in before checking the new draw.
    effective = cylinder.remaining_weight or 0.0
    if (
        entry is not None
        and entry.id is not None
        and entry.gas_recharge == cylinder.id
        and entry.gas_recharge_weight
    ):
        effective += entry.gas_recharge_weight
    if effective - weight < 0:
        raise BadRequest(
            f"cannot recharge {weight} from cylinder {cylinder_id}: only {effective} available"
        )


def _apply_gas(repair: Repairs, entry: RepairWorkLog, state, cylinder_id, weight, recovered) -> None:
    """Apply an already-validated gas dataset (mutation only)."""
    _restore_recharge(entry)
    entry.gas_system_state = state
    entry.gas_recharge = cylinder_id
    entry.gas_recharge_weight = weight if cylinder_id is not None else None
    entry.gas_recovered_weight = recovered
    if cylinder_id is not None:
        cylinder = db.session.get(GasCylinder, cylinder_id)
        cylinder.remaining_weight = (cylinder.remaining_weight or 0.0) - weight


def _restore_recharge(entry: RepairWorkLog) -> None:
    """Give back the recharged weight when its work-log entry goes away."""
    if entry.gas_recharge is None or entry.gas_recharge_weight is None:
        return
    cylinder = db.session.get(GasCylinder, entry.gas_recharge)
    if cylinder is not None:
        cylinder.remaining_weight = (cylinder.remaining_weight or 0.0) + entry.gas_recharge_weight


# --- repair CRUD ------------------------------------------------------------------

def _apply_repair_fields(repair: Repairs, data: dict) -> None:
    """Mutation-only; payload must already be validated."""
    if "type" in data and data["type"] is not None:
        repair.type = data["type"]
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
    if "start_data" in data and data["start_data"] is not None:
        repair.start_data = _parse_datetime(data["start_data"], "start_data")


def create_repair(data: dict) -> Repairs:
    if "type" not in data:
        raise BadRequest("type is required")
    _validate_repair_payload(data)
    parsed_parts = _validate_parts_payload(data.get("parts"))

    repair = Repairs()  # start_data uses the model default (now)
    _apply_repair_fields(repair, data)
    db.session.add(repair)
    db.session.flush()  # assign the id so part rows can reference it
    for item in parsed_parts:
        repair.parts.append(RepairPart(id_repairs=repair.id, **item))
    return repair


def get_repair(item_id: int) -> Repairs:
    repair = db.session.get(Repairs, item_id)
    if repair is None:
        raise NotFound(f"repair {item_id} not found")
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
    if params.get("type"):
        query = query.where(Repairs.type == params["type"])
    start_from = _parse_datetime(params.get("start_date_from"), "start_date_from")
    start_to = _parse_datetime(params.get("start_date_to"), "start_date_to")
    if start_from is not None:
        query = query.where(Repairs.start_data >= start_from)
    if start_to is not None:
        query = query.where(Repairs.start_data <= start_to)
    return list(db.session.execute(query).scalars().all())


def update_repair(repair: Repairs, data: dict) -> Repairs:
    _validate_repair_payload(data)
    parsed_parts = _validate_parts_payload(data["parts"]) if "parts" in data else None

    _apply_repair_fields(repair, data)
    if parsed_parts is not None:
        for existing in list(repair.parts):
            db.session.delete(existing)
        for item in parsed_parts:
            repair.parts.append(RepairPart(id_repairs=repair.id, **item))
    return repair


def delete_repair(repair: Repairs) -> None:
    """Delete a repair, restoring cylinder balances of its recharges first.

    The ORM cascade removes the work-log entries and part rows; the balance
    restore must happen before that, since each deleted entry that recorded
    a recharge must give its weight back to the cylinder (same transaction).
    """
    for entry in repair.work_log:
        _restore_recharge(entry)
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
    _validate_gas(repair, None, gas["state"], gas["cylinder"], gas["weight"], gas["recovered"])

    entry = RepairWorkLog(id_repairs=repair.id)
    _apply_non_gas_fields(entry, data)
    _apply_gas(
        repair,
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
    repair = entry.repair
    gas = _parse_work_log_gas(data) if _gas_fields_present(data) else None
    if gas is not None:
        # Read-only validation first, against the entry's current values.
        _validate_gas(repair, entry, gas["state"], gas["cylinder"], gas["weight"], gas["recovered"])

    _apply_non_gas_fields(entry, data)
    if gas is not None:
        _apply_gas(repair, entry, gas["state"], gas["cylinder"], gas["weight"], gas["recovered"])
    return entry


def delete_work_log_entry(entry: RepairWorkLog) -> None:
    _restore_recharge(entry)
    db.session.delete(entry)
