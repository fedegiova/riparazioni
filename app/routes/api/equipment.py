"""Equipment CRUD: refrigerators, gas cylinders, service parts (task group 3).

Delete-while-referenced is surfaced as HTTP 409: deleting a row that an
owned table still references violates the foreign-key constraint, and the
API IntegrityError handler renders it as a conflict (same behavior on
SQLite tests and on MSSQL in production).
"""

from flask import jsonify, request

from app.extensions import db
from app.models import GasCylinder, Refrigerator, ServicePart
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
    "picture_ref",
    "notes",
)


@bp.get("/gas-cylinders")
def list_gas_cylinders():
    items = (
        db.session.execute(db.select(GasCylinder).order_by(GasCylinder.id))
        .scalars()
        .all()
    )
    return jsonify([item.to_dict() for item in items])


@bp.post("/gas-cylinders")
def create_gas_cylinder():
    data = _json_body()
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


# --- Service parts -----------------------------------------------------------

PART_FIELDS = (
    "name",
    "supplier",
    "kind",
    "price",
    "is_refrigerator_part",
    "picture_ref",
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
