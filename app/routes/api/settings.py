"""Settings API: a JSON name/value store under ``/api/v1/settings``.

Values are exchanged as JSON documents (the text storage encoding is an
internal detail). Known settings are validated by the service, which also
synthesizes defaults for settings never written; a rejected write is a 400.
"""

import json

from flask import jsonify, request

from app.extensions import db
from app.routes.api import bp
from app.services import settings as settings_service
from app.services.errors import BadRequest


def _json_value():
    """Parse the request body as any JSON value (400 when it is not JSON)."""
    try:
        return json.loads(request.get_data(as_text=True))
    except (ValueError, TypeError):
        raise BadRequest("request body must be valid JSON") from None


@bp.get("/settings")
def list_settings():
    return jsonify(settings_service.list_settings())


@bp.get("/settings/<name>")
def get_setting(name):
    return jsonify(settings_service.get_setting(name))


@bp.put("/settings")
def update_settings():
    data = _json_value()
    if not isinstance(data, dict):
        raise BadRequest("settings body must be a JSON object of name/value pairs")
    settings_service.set_settings(data)
    db.session.commit()
    return jsonify(settings_service.list_settings())


@bp.put("/settings/<name>")
def put_setting(name):
    value = _json_value()
    settings_service.set_setting(name, value)
    db.session.commit()
    return jsonify(settings_service.get_setting(name))


@bp.delete("/settings/<name>")
def delete_setting(name):
    settings_service.delete_setting(name)
    db.session.commit()
    return "", 204
