"""Pictures: upload, list, detail, download, delete (task group 4).

Delete-while-referenced returns 409: gas cylinders and service parts hold a
``picture_ref`` foreign key, and the Picture model uses passive_deletes so
the constraint is what rejects the delete.
"""

from flask import jsonify, request, send_file

from app.extensions import db
from app.models import Picture
from app.routes.api import bp
from app.services import pictures as pictures_service
from app.services.errors import NotFound


def _get_or_404(item_id: int) -> Picture:
    picture = db.session.get(Picture, item_id)
    if picture is None:
        raise NotFound(f"picture {item_id} not found")
    return picture


@bp.get("/pictures")
def list_pictures():
    items = (
        db.session.execute(db.select(Picture).order_by(Picture.id)).scalars().all()
    )
    return jsonify([item.to_dict() for item in items])


@bp.post("/pictures")
def upload_picture():
    file_storage = request.files.get("file")
    if file_storage is None or not file_storage.filename:
        from app.services.errors import BadRequest

        raise BadRequest("a file field is required")
    uploaded_by = request.form.get("uploaded_by")
    picture = pictures_service.store_upload(file_storage, uploaded_by)
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
    db.session.commit()  # 409 (still referenced) is raised here, file untouched
    pictures_service.remove_file(picture)
    return "", 204
