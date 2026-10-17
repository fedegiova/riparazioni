"""Picture file storage service (task 4.1).

Files are stored under ``<UPLOAD_DIR>/pictures/<uuid4-hex><ext>`` and the
``PICTURES`` row keeps the path relative to ``UPLOAD_DIR`` (e.g.
``pictures/ab12...jpg``). Resolving a picture's file location always starts
from the stored relative path joined under ``UPLOAD_DIR`` — client input
never reaches the filesystem.
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Picture
from app.services.errors import BadRequest, NotFound


def _pictures_dir() -> Path:
    path = Path(current_app.config["UPLOAD_DIR"]) / "pictures"
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_upload(file_storage, uploaded_by: str | None) -> Picture:
    """Persist an uploaded file and return its Picture record (uncommitted)."""
    original = secure_filename(file_storage.filename or "")
    extension = Path(original).suffix if original else ""
    if not file_storage.filename:
        raise BadRequest("a file field is required")

    picture_dir = _pictures_dir()
    stored_name = uuid.uuid4().hex + extension
    target = picture_dir / stored_name
    file_storage.save(target)

    picture = Picture(
        path=f"pictures/{stored_name}",
        uploaded_by=uploaded_by,
        uploaded_date=datetime.now(UTC).replace(tzinfo=None),
    )
    db.session.add(picture)
    return picture


def resolve_path(picture: Picture) -> Path:
    """Absolute path of a stored picture, under UPLOAD_DIR (validated)."""
    base = Path(current_app.config["UPLOAD_DIR"]).resolve()
    target = (base / picture.path).resolve()
    if not str(target).startswith(str(base) + "/") or not target.is_file():
        raise NotFound(f"file for picture {picture.id} is missing on disk")
    return target


def remove_file(picture: Picture) -> None:
    """Remove a stored picture file from disk (errors are ignored).

    Call this only AFTER the database record deletion has been committed,
    so a failed (e.g. 409) delete never orphans the record from its file.
    """
    try:
        path = Path(current_app.config["UPLOAD_DIR"]) / picture.path
        if path.is_file():
            path.unlink()
    except OSError:
        pass
