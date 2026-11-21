"""Equipment CRUD: refrigerators, gas cylinders, service parts (task group 3).

Delete-while-referenced is surfaced as HTTP 409: deleting a row that an
owned table still references violates the foreign-key constraint, and the
API IntegrityError handler renders it as a conflict (same behavior on
SQLite tests and on MSSQL in production).
"""

from datetime import UTC, datetime
from datetime import date as date_cls, datetime, time

from flask import jsonify, request

from app.extensions import db
from app.models import GasCylinder, Refill, Refrigerator, RepairWorkLog, ServicePart
from app.routes.api import bp
from app.services.errors import BadRequest, NotFound


def _json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest("request body must be a JSON object")
    return data


def _get_or_404(model, item_id: int):
    item = db.session.get(model, item_id)
    if item is None:
        raise NotFound(f"{model.__name__.lower()} {item_id} not found")
    return item


# --- Refrigerators -----------------------------------------------------------

REFRIGERATOR_FIELDS = ("serial_nr", "model", "brand", "gas_kg", "notes")


@bp.get("/refrigerators")
def list_refrigerators():
    items = (
        db.session.execute(db.select(Refrigerator).order_by(Refrigerator.id))
        .scalars()
        .all()
    )
    return jsonify([item.to_dict() for item in items])


@bp.post("/refrigerators")
def create_refrigerator():
    data = _json_body()
    item = Refrigerator(**{k: data.get(k) for k in REFRIGERATOR_FIELDS})
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.get("/refrigerators/<int:item_id>")
def get_refrigerator(item_id):
    return jsonify(_get_or_404(Refrigerator, item_id).to_dict())


@bp.put("/refrigerators/<int:item_id>")
def update_refrigerator(item_id):
    item = _get_or_404(Refrigerator, item_id)
    data = _json_body()
    for key in REFRIGERATOR_FIELDS:
        if key in data:
            setattr(item, key, data[key])
    db.session.commit()
    return jsonify(item.to_dict())


@bp.delete("/refrigerators/<int:item_id>")
def delete_refrigerator(item_id):
    item = _get_or_404(Refrigerator, item_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204


# --- Gas cylinders -----------------------------------------------------------

CYLINDER_FIELDS = (
    "gas_kind",
    "serial_nr",
    "model",
    "full_weight",
    "remaining_weight",
    "notes",
)


def _validate_full_weight(data: dict, *, required: bool) -> None:
    """Full weight is mandatory on create and may not be nulled on update."""
    if "full_weight" not in data:
        if required:
            raise BadRequest("full_weight is required")
        return
    value = data["full_weight"]
    if value is None:
        raise BadRequest("full_weight is required")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise BadRequest("full_weight must be a number")


@bp.get("/gas-cylinders")
def list_gas_cylinders():
    query = db.select(GasCylinder).order_by(GasCylinder.id)
    raw_archived = request.args.get("archived")
    include_archived = raw_archived not in (None, "") and _parse_bool_flag(
        raw_archived, "archived"
    )
    if not include_archived:
        query = query.where(GasCylinder.archived.is_(False))
    items = db.session.execute(query).scalars().all()
    return jsonify([item.to_dict() for item in items])


@bp.post("/gas-cylinders")
def create_gas_cylinder():
    data = _json_body()
    _validate_full_weight(data, required=True)
    item = GasCylinder(**{k: data.get(k) for k in CYLINDER_FIELDS})
    # A brand-new cylinder starts full.
    if item.remaining_weight is None and item.full_weight is not None:
        item.remaining_weight = item.full_weight
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.get("/gas-cylinders/<int:item_id>")
def get_gas_cylinder(item_id):
    return jsonify(_get_or_404(GasCylinder, item_id).to_dict())


@bp.put("/gas-cylinders/<int:item_id>")
def update_gas_cylinder(item_id):
    item = _get_or_404(GasCylinder, item_id)
    data = _json_body()
    _validate_full_weight(data, required=False)
    # The balance is derived from the operation log; it may only be seeded at
    # creation and moved by refills and gas movements.
    if "remaining_weight" in data:
        raise BadRequest(
            "remaining_weight can only be set at creation; it changes through "
            "refills and gas movements"
        )
    for key in CYLINDER_FIELDS:
        if key in data:
            setattr(item, key, data[key])
    db.session.commit()
    return jsonify(item.to_dict())


@bp.delete("/gas-cylinders/<int:item_id>")
def delete_gas_cylinder(item_id):
    item = _get_or_404(GasCylinder, item_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204


@bp.post("/gas-cylinders/<int:item_id>/archive")
def archive_gas_cylinder(item_id):
    """Retire a cylinder that is below one quarter of its full weight."""
    item = _get_or_404(GasCylinder, item_id)
    if not item.archived:
        remaining = item.remaining_weight or 0.0
        if remaining >= item.full_weight / 4:
            raise BadRequest(
                "a cylinder can only be archived when its remaining weight "
                "is below one quarter of its full weight"
            )
        item.archived = True
        db.session.commit()
    return jsonify(item.to_dict())


@bp.post("/gas-cylinders/<int:item_id>/restore")
def restore_gas_cylinder(item_id):
    """Bring an archived cylinder back; its balance is left untouched."""
    item = _get_or_404(GasCylinder, item_id)
    if item.archived:
        item.archived = False
        db.session.commit()
    return jsonify(item.to_dict())


def _parse_refill_date(value):
    if value is None:
        return datetime.now(UTC).date()
    if not isinstance(value, str):
        raise BadRequest("date must be an ISO 8601 date")
    try:
        return date_cls.fromisoformat(value)
    except ValueError:
        raise BadRequest("date must be an ISO 8601 date") from None


@bp.get("/gas-cylinders/<int:item_id>/refills")
def list_gas_cylinder_refills(item_id):
    cylinder = _get_or_404(GasCylinder, item_id)
    refills = sorted(cylinder.refills, key=lambda refill: (refill.date, refill.id))
    return jsonify([refill.to_dict() for refill in refills])


@bp.post("/gas-cylinders/<int:item_id>/refills")
def create_gas_cylinder_refill(item_id):
    """Record a refill: the cylinder comes back full and is unarchived."""
    cylinder = _get_or_404(GasCylinder, item_id)
    data = _json_body()
    reference = data.get("reference")
    if reference is not None and not isinstance(reference, str):
        raise BadRequest("reference must be a string")
    refill = Refill(
        gas_cylinder_id=cylinder.id,
        date=_parse_refill_date(data.get("date")),
        reference=reference,
    )
    cylinder.remaining_weight = cylinder.full_weight
    cylinder.archived = False
    db.session.add(refill)
    db.session.commit()
    return jsonify(refill.to_dict()), 201


# Gas-system states map to the operation kind reported in the cylinder log.
_GAS_MOVEMENT_KINDS = {
    "VUOTO": "recharge",
    "RECUPERO": "recovery",
    "RICUPERO_RICARICA": "recovery_recharge",
}
# Deterministic tie-break when two operations share the same time.
_OPERATION_ORDER = {
    "refill": 0,
    "recharge": 1,
    "recovery": 2,
    "recovery_recharge": 3,
}


def _cylinder_operations(cylinder: GasCylinder) -> list[dict]:
    """Merge a cylinder's refills and gas movements into one newest-first log.

    Derived on read from ``REFILLS`` and the ``REPAIR_WORK_LOG`` rows that
    reference the cylinder; nothing is persisted. Each entry carries its source
    reference (the refill's reference text, or the work-log entry's repair id,
    entry id, and operator) and the cylinder's remaining weight after it.
    """
    dated: list[tuple[datetime, int, int, dict]] = []

    for refill in cylinder.refills:
        when = (
            datetime.combine(refill.date, time.min) if refill.date else datetime.min
        )
        dated.append(
            (
                when,
                _OPERATION_ORDER["refill"],
                refill.id or 0,
                {
                    "kind": "refill",
                    "id": refill.id,
                    "date": refill.date.isoformat() if refill.date else None,
                    "reference": refill.reference,
                },
            )
        )

    movements = (
        db.session.execute(
            db.select(RepairWorkLog).where(RepairWorkLog.gas_recharge == cylinder.id)
        )
        .scalars()
        .all()
    )
    for entry in movements:
        kind = _GAS_MOVEMENT_KINDS.get(entry.gas_system_state)
        if kind is None:
            # Not a gas-affecting movement (e.g. PIENO, or no state): skip.
            continue
        when = entry.start_time or entry.end_time
        dated.append(
            (
                when or datetime.min,
                _OPERATION_ORDER[kind],
                entry.id or 0,
                {
                    "kind": kind,
                    "date": when.isoformat() if when else None,
                    "repair_id": entry.id_repairs,
                    "work_log_id": entry.id,
                    "operator": entry.operator,
                    "gas_system_state": entry.gas_system_state,
                    "recharged_weight": entry.gas_recharge_weight,
                    "recovered_weight": entry.gas_recovered_weight,
                },
            )
        )

    # Replay oldest-first from the cylinder's full weight at creation to attach
    # each entry's resulting balance, then flip back to newest-first.
    dated.sort(key=lambda item: (item[0], item[1], item[2]))

    full = cylinder.full_weight or 0.0
    balance = full
    for _, _, _, entry in dated:
        kind = entry["kind"]
        if kind == "refill":
            balance = full
        elif kind == "recharge":
            balance -= entry["recharged_weight"] or 0.0
        elif kind == "recovery":
            balance += entry["recovered_weight"] or 0.0
        elif kind == "recovery_recharge":
            balance += entry["recovered_weight"] or 0.0
            balance -= entry["recharged_weight"] or 0.0
        entry["remaining_weight"] = round(balance, 6)

    dated.reverse()
    return [item[3] for item in dated]


@bp.get("/gas-cylinders/<int:item_id>/operations")
def list_gas_cylinder_operations(item_id):
    """The cylinder's gas-affecting history: refills plus gas movements."""
    cylinder = _get_or_404(GasCylinder, item_id)
    return jsonify(_cylinder_operations(cylinder))


# --- Service parts -----------------------------------------------------------

PART_FIELDS = (
    "name",
    "supplier",
    "kind",
    "price",
    "is_refrigerator_part",
    "notes",
)


def _parse_bool_flag(value, name: str):
    if value in (True, False):
        return value
    if isinstance(value, str) and value.lower() in ("true", "1"):
        return True
    if isinstance(value, str) and value.lower() in ("false", "0"):
        return False
    raise BadRequest(f"{name} must be a boolean")


@bp.get("/service-parts")
def list_service_parts():
    query = db.select(ServicePart).order_by(ServicePart.id)
    raw_flag = request.args.get("is_refrigerator_part")
    if raw_flag is not None and raw_flag != "":
        query = query.where(
            ServicePart.is_refrigerator_part.is_(
                _parse_bool_flag(raw_flag, "is_refrigerator_part")
            )
        )
    items = db.session.execute(query).scalars().all()
    return jsonify([item.to_dict() for item in items])


@bp.post("/service-parts")
def create_service_part():
    data = _json_body()
    if "is_refrigerator_part" in data:
        data = dict(data)
        data["is_refrigerator_part"] = _parse_bool_flag(
            data["is_refrigerator_part"], "is_refrigerator_part"
        )
    item = ServicePart(**{k: data.get(k) for k in PART_FIELDS})
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.get("/service-parts/<int:item_id>")
def get_service_part(item_id):
    return jsonify(_get_or_404(ServicePart, item_id).to_dict())


@bp.put("/service-parts/<int:item_id>")
def update_service_part(item_id):
    item = _get_or_404(ServicePart, item_id)
    data = _json_body()
    if "is_refrigerator_part" in data:
        data = dict(data)
        data["is_refrigerator_part"] = _parse_bool_flag(
            data["is_refrigerator_part"], "is_refrigerator_part"
        )
    for key in PART_FIELDS:
        if key in data:
            setattr(item, key, data[key])
    db.session.commit()
    return jsonify(item.to_dict())


@bp.delete("/service-parts/<int:item_id>")
def delete_service_part(item_id):
    item = _get_or_404(ServicePart, item_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204
