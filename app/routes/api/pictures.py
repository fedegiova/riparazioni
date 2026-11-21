"""Pictures: upload, list, detail, download, delete.

A picture belongs to exactly one owner (``owner_type``/``owner_id``), set at
upload time. There is no separate reference to protect, so deleting a picture
is never a conflict.
"""

from flask import jsonify, request, send_file

from app.extensions import db
from app.models import Picture
from app.routes.api import bp
from app.services import pictures as pictures_service
from app.services.errors import BadRequest, NotFound


def _get_or_404(item_id: int) -> Picture:
    picture = db.session.get(Picture, item_id)
    if picture is None:
        raise NotFound(f"picture {item_id} not found")
    return picture


def _owner_filter():
    """The optional owner filter, or ``(None, None)`` when absent (400 if half)."""
    owner_type = request.args.get("owner_type")
    owner_id = request.args.get("owner_id")
    if (owner_type is None) != (owner_id is None):
        raise BadRequest("owner_type and owner_id must be provided together")
    if owner_type is None:
        return None, None
    try:
        return owner_type, int(owner_id)
    except (TypeError, ValueError):
        raise BadRequest("owner_id must be an integer") from None


@bp.get("/pictures")
def list_pictures():
    query = db.select(Picture).order_by(Picture.id)
    owner_type, owner_id = _owner_filter()
    if owner_type is not None:
        query = query.where(
            Picture.owner_type == owner_type, Picture.owner_id == owner_id
        )
    items = db.session.execute(query).scalars().all()
    return jsonify([item.to_dict() for item in items])


@bp.post("/pictures")
def upload_picture():
    picture = pictures_service.store_upload(
        request.files.get("file"),
        request.form.get("owner_type"),
        request.form.get("owner_id"),
        request.form.get("uploaded_by"),
    )
    db.session.commit()
    return jsonify(picture.to_dict()), 201


@bp.get("/pictures/<int:item_id>")
def get_picture(item_id):
    return jsonify(_get_or_404(item_id).to_dict())


@bp.get("/pictures/<int:item_id>/file")
def download_picture(item_id):
    picture = _get_or_404(item_id)
    path = pictures_service.resolve_path(picture)
    return send_file(path)


@bp.delete("/pictures/<int:item_id>")
def delete_picture(item_id):
    picture = _get_or_404(item_id)
    db.session.delete(picture)
    db.session.commit()
    pictures_service.remove_file(picture)
    return "", 204
