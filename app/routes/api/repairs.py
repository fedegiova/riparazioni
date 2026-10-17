"""Repairs CRUD, work log, and gas-recharge operations (task group 5).

The business rules live in app/services/repairs.py; these handlers only
translate between HTTP and the service, and commit at the end of each
mutating request so related writes share one transaction.
"""

from flask import jsonify, request

from app.extensions import db
from app.routes.api import bp
from app.services import repairs as repairs_service
from app.services.errors import BadRequest


def _json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest("request body must be a JSON object")
    return data


# --- Repairs ------------------------------------------------------------------

@bp.get("/repairs")
def list_repairs():
    repairs = repairs_service.list_repairs(request.args)
    return jsonify([repair.to_dict() for repair in repairs])


@bp.post("/repairs")
def create_repair():
    repair = repairs_service.create_repair(_json_body())
    db.session.commit()
    return jsonify(repair.to_dict(include_details=True)), 201


@bp.get("/repairs/<int:item_id>")
def get_repair(item_id):
    repair = repairs_service.get_repair(item_id)
    return jsonify(repair.to_dict(include_details=True))


@bp.put("/repairs/<int:item_id>")
def update_repair(item_id):
    repair = repairs_service.get_repair(item_id)
    repairs_service.update_repair(repair, _json_body())
    db.session.commit()
    return jsonify(repair.to_dict(include_details=True))


@bp.delete("/repairs/<int:item_id>")
def delete_repair(item_id):
    repair = repairs_service.get_repair(item_id)
    repairs_service.delete_repair(repair)  # restores balances, then cascades
    db.session.commit()
    return "", 204


# --- Work log -----------------------------------------------------------------

@bp.get("/repairs/<int:repair_id>/work-log")
def list_work_log(repair_id):
    repair = repairs_service.get_repair(repair_id)
    return jsonify([entry.to_dict() for entry in repair.work_log])


@bp.post("/repairs/<int:repair_id>/work-log")
def add_work_log_entry(repair_id):
    repair = repairs_service.get_repair(repair_id)
    entry = repairs_service.add_work_log_entry(repair, _json_body())
    db.session.commit()
    return jsonify(entry.to_dict()), 201


@bp.put("/repairs/<int:repair_id>/work-log/<int:entry_id>")
def update_work_log_entry(repair_id, entry_id):
    repair = repairs_service.get_repair(repair_id)
    entry = repairs_service.get_work_log_entry(repair, entry_id)
    repairs_service.update_work_log_entry(entry, _json_body())
    db.session.commit()
    return jsonify(entry.to_dict())


@bp.delete("/repairs/<int:repair_id>/work-log/<int:entry_id>")
def delete_work_log_entry(repair_id, entry_id):
    repair = repairs_service.get_repair(repair_id)
    entry = repairs_service.get_work_log_entry(repair, entry_id)
    repairs_service.delete_work_log_entry(entry)
    db.session.commit()
    return "", 204
