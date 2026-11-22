"""Repair business logic (task group 5).

Owns the validation rules that the database cannot express:
- customer/vehicle must exist in the legacy reference data (no DB FK,
  because VICLIENTI is a view and the migration must not touch
  DATIDBSTORICO),
- gas-recharge bookkeeping: a recharge decreases the cylinder's remaining
  weight in the same transaction; deleting the entry restores it.

Read-time computed fields (`total_hours`, `customer_name`) are attached to
the repair instances before serialization. `total_hours` is stored only as the
archive snapshot (`archived_total_hours`); active repairs always recompute it.

Every mutating function follows validate-first semantics: all checks run
(read-only) before the session is touched, so a rejected request (400/409)
never leaves partially mutated state behind. Functions do NOT commit — the
route commits, keeping related writes in one transaction.
"""

import math
from io import BytesIO

from openpyxl import Workbook

from app.extensions import db
from app.models import (
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
from app.services.errors import BadRequest, Conflict, NotFound
from app.services.guard import acquire
from app.services.settings import get_setting
from app.services.working_time import Calendar, entry_hours

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


def _is_date_only(value) -> bool:
    """True when *value* is a date string with no time component.

    Used to widen a range's upper bound to the whole day: `_parse_datetime`
    turns a date-only value into midnight at the start of that day.
    """
    if not isinstance(value, str):
        return False
    from datetime import date

    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


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

GAS_OPERATIONS = ("none", "fill", "recovery", "recovery_recharge")
# Payload keys from the retired gas-state contract. Their presence is reported
# as an unsupported payload rather than silently ignored.
_LEGACY_GAS_KEYS = ("gas_system_state", "gas_recharge_weight", "gas_recovered_weight")


def _parse_work_log_gas(data: dict) -> dict:
    operation = data.get("gas_operation")
    if operation == "":
        operation = None
    if operation is None and any(key in data for key in _LEGACY_GAS_KEYS):
        raise BadRequest(
            "gas_system_state-based payloads are no longer supported; "
            "use gas_operation"
        )
    return {
        "operation": operation,
        "cylinder": data.get("gas_recharge"),
        "measured": data.get("gas_measured_kg"),
        "expected": data.get("expected_refrigerator"),
    }


def _is_finite_number(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _require_measured(value, operation: str) -> float:
    if not _is_finite_number(value):
        raise BadRequest(f"{operation} requires a finite gas_measured_kg in kg")
    return float(value)


def _validate_gas_type(refrigerator, cylinder) -> None:
    if not refrigerator.gas_kind or not cylinder.gas_kind:
        raise BadRequest(
            "both the refrigerator and the cylinder must have a gas type"
        )
    if refrigerator.gas_kind != cylinder.gas_kind:
        raise BadRequest(
            f"gas type mismatch: refrigerator {refrigerator.gas_kind} vs "
            f"cylinder {cylinder.gas_kind}"
        )


def _resolve_gas_refrigerator(repair: Repairs, expected):
    """The refrigerator a gas movement belongs to, or a blocking error.

    Until the repair is locked, the unit installed on its allestimento is the
    one used and then frozen. Once locked, only that recorded unit counts, and
    it must still be installed on this allestimento.
    """
    if repair.vehicle is None:
        raise BadRequest(
            "gas operations require the repair to have an allestimento"
        )

    if repair.gas_equipment_locked:
        refrigerator = (
            db.session.get(Refrigerator, repair.refrigerator)
            if repair.refrigerator is not None
            else None
        )
        if refrigerator is None or refrigerator.allestimento_id != repair.vehicle:
            raise Conflict(
                "the repair's refrigerator is no longer installed on its "
                "allestimento; record gas work for the replacement on a "
                "separate repair"
            )
    else:
        refrigerator = db.session.execute(
            db.select(Refrigerator).where(
                Refrigerator.allestimento_id == repair.vehicle
            )
        ).scalars().first()
        if refrigerator is None:
            raise BadRequest(
                f"no refrigerator is installed on allestimento {repair.vehicle}; "
                "add one in Anagrafica"
            )

    if expected is not None and expected != refrigerator.id:
        raise Conflict(
            "the installed refrigerator changed since the form was loaded; "
            "reload and retry"
        )
    return refrigerator


def _stored_delta(entry: RepairWorkLog) -> float:
    """The cylinder balance change this entry applied, in kg.

    Negative for fill and the net part of a combined operation (gas leaves the
    cylinder), positive for a recovery. Zero for ordinary work.
    """
    measured = entry.gas_measured_kg or 0.0
    if entry.gas_operation == "fill":
        return -measured
    if entry.gas_operation == "recovery":
        return measured
    if entry.gas_operation == "recovery_recharge":
        return -measured
    return 0.0


def _validate_gas(entry, repair: Repairs, gas: dict):
    """Read-only validation of a gas dataset.

    Returns ``(movement, refrigerator)`` where ``movement`` is the normalized
    change to apply (or ``None`` for ordinary work), or raises. Never mutates
    the session, so a rejected request changes no stock, lock, or timer.

    Field matrix::

        operation           cylinder   measured (kg)        meaning
        none                forbidden  forbidden            ordinary work
        fill                required   required (>0, <=C)    gas added
        recovery            required   required (>=0)        gas recovered
        recovery_recharge   required   required (0..C)       net gas added
    """
    operation = gas["operation"]
    cylinder_id = gas["cylinder"]
    measured = gas["measured"]
    expected = gas["expected"]
    has_cylinder = cylinder_id is not None
    has_measured = measured is not None

    if operation is None:
        if has_cylinder or has_measured:
            raise BadRequest("an entry carrying gas data requires a gas_operation")
        return None, None

    if operation not in GAS_OPERATIONS:
        raise BadRequest(
            f"gas_operation must be one of {', '.join(GAS_OPERATIONS)}"
        )

    if operation == "none":
        if has_cylinder or has_measured:
            raise BadRequest(
                "none entries must not carry cylinder or weight data"
            )
        return None, None

    refrigerator = _resolve_gas_refrigerator(repair, expected)

    if not has_cylinder:
        raise BadRequest(f"{operation} requires a gas_recharge cylinder")
    cylinder = db.session.get(GasCylinder, cylinder_id)
    if cylinder is None:
        raise Conflict(f"cylinder {cylinder_id} does not exist")
    _validate_gas_type(refrigerator, cylinder)

    nameplate = refrigerator.gas_kg
    if operation == "fill":
        amount = _require_measured(measured, "fill")
        if amount <= 0:
            raise BadRequest("fill requires a positive gas_measured_kg")
        if amount > nameplate:
            raise BadRequest(
                "the fill amount exceeds the refrigerator nameplate capacity"
            )
        delta, recharged, recovered, stored_nameplate = -amount, amount, 0.0, None
    elif operation == "recovery":
        amount = _require_measured(measured, "recovery")
        if amount < 0:
            raise BadRequest("recovery requires a non-negative gas_measured_kg")
        delta, recharged, recovered, stored_nameplate = amount, 0.0, amount, None
    else:  # recovery_recharge
        amount = _require_measured(measured, "recovery_recharge")
        if amount < 0 or amount > nameplate:
            raise BadRequest(
                "the combined net added gas must be between 0 and the "
                "nameplate capacity"
            )
        delta = -amount
        recharged = nameplate
        recovered = nameplate - amount
        stored_nameplate = nameplate

    # A movement must keep the cylinder within [0, full weight]. When this
    # entry already moved gas through the same cylinder, validate against the
    # balance as if that movement had been undone.
    effective = cylinder.remaining_weight or 0.0
    if entry is not None and entry.id is not None and entry.gas_recharge == cylinder.id:
        effective -= _stored_delta(entry)
    result = effective + delta
    if result < 0:
        raise BadRequest(
            f"cannot recharge {delta * -1} from cylinder {cylinder_id}: "
            f"only {effective} available"
        )
    if result > cylinder.full_weight:
        raise BadRequest(
            f"recovering {recovered} would exceed cylinder {cylinder_id} "
            f"full weight {cylinder.full_weight}"
        )

    movement = {
        "operation": operation,
        "cylinder": cylinder.id,
        "measured": float(measured),
        "nameplate": stored_nameplate,
        "delta": delta,
        "recharged": recharged,
        "recovered": recovered,
        "refrigerator": refrigerator.id,
    }
    return movement, refrigerator


def _apply_gas(
    entry: RepairWorkLog, movement, refrigerator, repair: Repairs
) -> None:
    """Apply an already-validated gas movement (mutation only).

    Reverses the entry's previous movement first, then stores the new one and
    updates the cylinder balance and the repair's equipment lock.
    """
    _reverse_gas(entry)
    entry.gas_operation = movement["operation"]
    entry.gas_recharge = movement["cylinder"]
    entry.gas_measured_kg = movement["measured"]
    entry.gas_nameplate_kg = movement["nameplate"]
    # Clear any retired-contract values a legacy row may still carry.
    entry.gas_system_state = None
    entry.gas_recharge_weight = None
    entry.gas_recovered_weight = None

    cylinder = db.session.get(GasCylinder, movement["cylinder"])
    cylinder.remaining_weight = (cylinder.remaining_weight or 0.0) + movement["delta"]

    repair.refrigerator = refrigerator.id
    repair.gas_equipment_locked = True


def _clear_gas(entry: RepairWorkLog) -> None:
    """Reverse the entry's movement and return it to ordinary work."""
    _reverse_gas(entry)
    entry.gas_operation = None
    entry.gas_recharge = None
    entry.gas_measured_kg = None
    entry.gas_nameplate_kg = None
    entry.gas_system_state = None
    entry.gas_recharge_weight = None
    entry.gas_recovered_weight = None


def _reverse_gas(entry: RepairWorkLog) -> None:
    """Undo the entry's gas movement when it is updated, cleared, or removed."""
    if entry.gas_recharge is None:
        return
    cylinder = db.session.get(GasCylinder, entry.gas_recharge)
    if cylinder is not None:
        cylinder.remaining_weight = (
            (cylinder.remaining_weight or 0.0) - _stored_delta(entry)
        )


# --- read-time computed fields ----------------------------------------------------

def _calendar() -> Calendar:
    """Workshop calendar for one calculation batch.

    Settings are read through the settings service, so an unwritten schedule
    resolves to its default and a rejected write never affects this read.
    """
    return Calendar.from_settings(
        get_setting("working_hours"), get_setting("holidays")
    )


def _running_entries(repair_id: int) -> list[RepairWorkLog]:
    """Work logs that have begun and have no end time yet."""
    return list(
        db.session.execute(
            db.select(RepairWorkLog)
            .where(
                RepairWorkLog.id_repairs == repair_id,
                RepairWorkLog.start_time.is_not(None),
                RepairWorkLog.end_time.is_(None),
            )
            .order_by(RepairWorkLog.id)
        ).scalars()
    )


def _freeze_total(repair: Repairs) -> None:
    """Store the calendar-adjusted total of a repair that is being archived."""
    entries = db.session.execute(
        db.select(RepairWorkLog).where(RepairWorkLog.id_repairs == repair.id)
    ).scalars()
    calendar = _calendar()
    repair.archived_total_hours = sum(
        entry_hours(entry.start_time, entry.end_time, calendar) for entry in entries
    )


def _ensure_archivable(repair: Repairs) -> None:
    """Refuse to archive while a timer is still running."""
    running = _running_entries(repair.id)
    if not running:
        return
    labels = ", ".join(
        f"#{entry.id}" + (f" ({entry.operator})" if entry.operator else "")
        for entry in running
    )
    raise Conflict(
        "repair has running work logs; stop them before archiving: " + labels
    )


def _ensure_active(repair: Repairs) -> None:
    """Archived repairs are read-only until explicitly reopened."""
    if repair.end_data is not None:
        raise Conflict(
            f"repair {repair.id} is archived; reopen it before changing its work log"
        )


def _handoff_operator_timer(operator: str, start) -> None:
    """Stop the operator's running timers at *start* (same or other repairs).

    Only running entries on active repairs are touched: an archived repair is
    read-only, and a completed historical entry never stops a timer. Legacy
    duplicates for the operator are closed at the same boundary. Backdating a
    start before a running timer's own start would produce a negative interval,
    so it is rejected and nothing is stopped.
    """
    rows = db.session.execute(
        db.select(RepairWorkLog)
        .join(Repairs, Repairs.id == RepairWorkLog.id_repairs)
        .where(
            RepairWorkLog.operator == operator,
            RepairWorkLog.start_time.is_not(None),
            RepairWorkLog.end_time.is_(None),
            Repairs.end_data.is_(None),
        )
        .order_by(RepairWorkLog.id)
    ).scalars().all()
    for row in rows:
        if row.start_time > start:
            raise Conflict(
                f"work log #{row.id} ({operator}) started at "
                f"{row.start_time.isoformat()}; the new entry starts earlier"
            )
        row.end_time = start


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

    A single query loads the work-log entries and recharged weights of every
    listed repair (no per-repair query); customer names are resolved for the
    distinct ids in one lookup. Unknown customer ids resolve to a null name.

    `total_hours` is the live calendar-adjusted total for an active repair and
    the stored snapshot for an archived one, so later calendar edits cannot
    rewrite a finalized figure.
    """
    ids = [repair.id for repair in repairs]
    hours: dict[int, float] = {}
    gas: dict[int, float] = {}
    pictures: dict[int, list] = {}
    calendar = _calendar()
    if ids:
        entries = db.session.execute(
            db.select(RepairWorkLog).where(RepairWorkLog.id_repairs.in_(ids))
        ).scalars()
        for entry in entries:
            hours[entry.id_repairs] = hours.get(entry.id_repairs, 0.0) + entry_hours(
                entry.start_time, entry.end_time, calendar
            )
            gas[entry.id_repairs] = gas.get(entry.id_repairs, 0.0) + (
                entry.recharged_kg() or 0.0
            )
        owned = db.session.execute(
            db.select(Picture)
            .where(Picture.owner_type == "repair", Picture.owner_id.in_(ids))
            .order_by(Picture.id)
        ).scalars()
        for picture in owned:
            pictures.setdefault(picture.owner_id, []).append(picture)
    names = _resolve_customer_names({repair.customer for repair in repairs})
    # Whether each repair's recorded refrigerator is still installed on its
    # allestimento (None when no unit is recorded), in one lookup.
    refrigerator_ids = {
        repair.refrigerator for repair in repairs if repair.refrigerator is not None
    }
    refrigerator_allestimento: dict[int, int | None] = {}
    if refrigerator_ids:
        rows = db.session.execute(
            db.select(Refrigerator.id, Refrigerator.allestimento_id).where(
                Refrigerator.id.in_(refrigerator_ids)
            )
        ).all()
        refrigerator_allestimento = {row[0]: row[1] for row in rows}
    for repair in repairs:
        if repair.end_data is not None and repair.archived_total_hours is not None:
            repair.total_hours = repair.archived_total_hours
        else:
            repair.total_hours = hours.get(repair.id, 0.0)
        repair.gas_used = gas.get(repair.id, 0.0)
        repair.customer_name = names.get(repair.customer)
        repair.pictures = pictures.get(repair.id, [])
        if repair.refrigerator is None:
            repair.refrigerator_installed = None
        else:
            repair.refrigerator_installed = (
                refrigerator_allestimento.get(repair.refrigerator) == repair.vehicle
            )


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
    if repair.end_data is not None:
        # Created already closed: no work logs can exist yet, so the frozen
        # total is zero until the repair is reopened and worked on.
        repair.archived_total_hours = 0.0
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
        if _is_date_only(params.get("start_date_to")):
            # A date-only upper bound covers the whole selected day, so use a
            # half-open comparison against the following midnight.
            from datetime import timedelta

            query = query.where(Repairs.start_data < start_to + timedelta(days=1))
        else:
            query = query.where(Repairs.start_data <= start_to)
    repairs = list(db.session.execute(query).scalars().all())
    _decorate_repairs(repairs)
    return repairs


def update_repair(repair: Repairs, data: dict) -> Repairs:
    _validate_repair_payload(data)
    parsed_parts = _validate_parts_payload(data["parts"]) if "parts" in data else None

    acquire()
    db.session.refresh(repair)

    # Once gas work locked the equipment, the vehicle and refrigerator are
    # frozen so a later replacement cannot silently re-point the repair.
    if repair.gas_equipment_locked:
        if "vehicle" in data and data["vehicle"] != repair.vehicle:
            raise Conflict(
                "the repair's equipment is locked by gas work; its vehicle "
                "cannot change"
            )
        if "refrigerator" in data and data["refrigerator"] != repair.refrigerator:
            raise Conflict(
                "the repair's refrigerator is locked by gas work; it cannot change"
            )

    was_archived = repair.end_data is not None
    if "end_data" in data:
        new_end = _parse_datetime(data["end_data"], "end_data")
        if new_end is not None and not was_archived:
            _ensure_archivable(repair)
            _freeze_total(repair)
        elif new_end is None and was_archived:
            # Reopening restores live calculation; the next archive freezes a
            # new total from the calendar and logs in effect then.
            repair.archived_total_hours = None

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
    acquire()
    db.session.refresh(repair)
    for entry in repair.work_log:
        _reverse_gas(entry)
    db.session.delete(repair)


# --- work log ------------------------------------------------------------------------

def _configured_operators() -> list[str]:
    """Operator names from settings; an unwritten setting uses its default."""
    operators = get_setting("operators")
    return operators if isinstance(operators, list) else []


def _validate_new_operator(value) -> None:
    """A new work log must name a configured operator."""
    if not isinstance(value, str) or not value:
        raise BadRequest("operator is required")
    if value not in _configured_operators():
        raise BadRequest(f"operator {value!r} is not configured")


def _validate_operator_update(entry: RepairWorkLog, value) -> None:
    """Allow an unchanged legacy operator; a change must be configured.

    Legacy entries may carry an operator that is no longer in settings. Editing
    such an entry without touching its operator stays possible; switching to a
    different name requires one from the configured list.
    """
    if value in (None, ""):
        return
    if not isinstance(value, str):
        raise BadRequest("operator must be a string")
    if value == entry.operator:
        return
    if value not in _configured_operators():
        raise BadRequest(f"operator {value!r} is not configured")


def _validate_description(value) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise BadRequest("description must be a string")
    if len(value) > 4000:
        raise BadRequest("description must be at most 4000 characters")


def _apply_non_gas_fields(entry: RepairWorkLog, data: dict) -> None:
    if "start_time" in data:
        entry.start_time = _parse_datetime(data["start_time"], "start_time")
    if "end_time" in data:
        entry.end_time = _parse_datetime(data["end_time"], "end_time")
    if "operator" in data:
        entry.operator = data["operator"]
    if "description" in data:
        entry.description = data["description"] or None


def _gas_fields_present(data: dict) -> bool:
    return any(
        key in data
        for key in (
            "gas_operation",
            "gas_recharge",
            "gas_measured_kg",
            *_LEGACY_GAS_KEYS,
        )
    )


def add_work_log_entry(repair: Repairs, data: dict) -> RepairWorkLog:
    acquire()
    db.session.refresh(repair)
    _ensure_active(repair)
    _validate_new_operator(data.get("operator"))
    _validate_description(data.get("description"))

    # Validate the whole gas dataset (read-only) before any timer handoff or
    # equipment lock, so a rejected request changes nothing.
    gas = _parse_work_log_gas(data)
    movement, refrigerator = _validate_gas(None, repair, gas)

    entry = RepairWorkLog(id_repairs=repair.id)
    _apply_non_gas_fields(entry, data)
    if entry.start_time is not None and entry.end_time is None:
        _handoff_operator_timer(entry.operator, entry.start_time)
    if movement is not None:
        _apply_gas(entry, movement, refrigerator, repair)
    else:
        _clear_gas(entry)
    db.session.add(entry)
    return entry


def get_work_log_entry(repair: Repairs, entry_id: int) -> RepairWorkLog:
    entry = db.session.get(RepairWorkLog, entry_id)
    if entry is None or entry.id_repairs != repair.id:
        raise NotFound(f"work-log entry {entry_id} not found for repair {repair.id}")
    return entry


def update_work_log_entry(entry: RepairWorkLog, data: dict) -> RepairWorkLog:
    acquire()
    db.session.refresh(entry)
    repair = entry.repair
    db.session.refresh(repair)
    _ensure_active(repair)
    if "operator" in data:
        _validate_operator_update(entry, data["operator"])
    if "description" in data:
        _validate_description(data["description"])

    gas_present = _gas_fields_present(data)
    movement = refrigerator = None
    if gas_present:
        # Read-only validation first, against the entry's current values.
        gas = _parse_work_log_gas(data)
        movement, refrigerator = _validate_gas(entry, repair, gas)

    _apply_non_gas_fields(entry, data)
    if gas_present:
        if movement is not None:
            _apply_gas(entry, movement, refrigerator, repair)
        else:
            _clear_gas(entry)
    return entry


def delete_work_log_entry(entry: RepairWorkLog) -> None:
    acquire()
    db.session.refresh(entry)
    repair = entry.repair
    db.session.refresh(repair)
    _ensure_active(repair)
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
