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

from io import BytesIO

from openpyxl import Workbook

from app.extensions import db
from app.models import (
    GAS_SYSTEM_STATES,
    Customer,
    GasCylinder,
    Picture,
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
                entry.gas_recharge_weight or 0.0
            )
        owned = db.session.execute(
            db.select(Picture)
            .where(Picture.owner_type == "repair", Picture.owner_id.in_(ids))
            .order_by(Picture.id)
        ).scalars()
        for picture in owned:
            pictures.setdefault(picture.owner_id, []).append(picture)
    names = _resolve_customer_names({repair.customer for repair in repairs})
    for repair in repairs:
        if repair.end_data is not None and repair.archived_total_hours is not None:
            repair.total_hours = repair.archived_total_hours
        else:
            repair.total_hours = hours.get(repair.id, 0.0)
        repair.gas_used = gas.get(repair.id, 0.0)
        repair.customer_name = names.get(repair.customer)
        repair.pictures = pictures.get(repair.id, [])


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
            "gas_system_state",
            "gas_recharge",
            "gas_recharge_weight",
            "gas_recovered_weight",
        )
    )


def add_work_log_entry(repair: Repairs, data: dict) -> RepairWorkLog:
    acquire()
    db.session.refresh(repair)
    _ensure_active(repair)
    _validate_new_operator(data.get("operator"))
    _validate_description(data.get("description"))

    gas = _parse_work_log_gas(data)
    _validate_gas(None, gas["state"], gas["cylinder"], gas["weight"], gas["recovered"])

    entry = RepairWorkLog(id_repairs=repair.id)
    _apply_non_gas_fields(entry, data)
    if entry.start_time is not None and entry.end_time is None:
        _handoff_operator_timer(entry.operator, entry.start_time)
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
    acquire()
    db.session.refresh(entry)
    repair = entry.repair
    db.session.refresh(repair)
    _ensure_active(repair)
    if "operator" in data:
        _validate_operator_update(entry, data["operator"])
    if "description" in data:
        _validate_description(data["description"])

    gas = _parse_work_log_gas(data) if _gas_fields_present(data) else None
    if gas is not None:
        # Read-only validation first, against the entry's current values.
        _validate_gas(entry, gas["state"], gas["cylinder"], gas["weight"], gas["recovered"])

    _apply_non_gas_fields(entry, data)
    if gas is not None:
        _apply_gas(entry, gas["state"], gas["cylinder"], gas["weight"], gas["recovered"])
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
