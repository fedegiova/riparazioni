"""Picture file storage service.

Files are stored under ``<UPLOAD_DIR>/<owner_type>/YYYY-MM-DD-SEQ.<ext>`` and
the ``PICTURES`` row keeps the path relative to ``UPLOAD_DIR`` (e.g.
``repair/2026-11-21-0007.jpg``). ``SEQ`` is a per-owner-type, per-day sequence
zero-padded to four digits; the unique constraint on ``PICTURES.path`` is the
real collision guard, so the sequence is only a hint and the insert is retried.

Resolving a picture's file location always starts from the stored relative path
joined under ``UPLOAD_DIR`` — client input never reaches the filesystem.
"""

import mimetypes
from datetime import UTC, datetime
from pathlib import Path

from flask import current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import GasCylinder, Picture, Repairs, ServicePart
from app.services.errors import BadRequest, Conflict, NotFound

# A picture is always attached to exactly one of these owners (no junction
# table): a repair, a spare (service part), or a gas cylinder.
OWNER_TYPES = ("repair", "spare", "cylinder")
_OWNER_MODELS = {"repair": Repairs, "spare": ServicePart, "cylinder": GasCylinder}
_MAX_SEQUENCE_ATTEMPTS = 5


def _owner_dir(owner_type: str) -> Path:
    path = Path(current_app.config["UPLOAD_DIR"]) / owner_type
    path.mkdir(parents=True, exist_ok=True)
    return path


def _parse_owner_id(raw) -> int:
    if raw is None or str(raw).strip() == "":
        raise BadRequest("owner_id is required")
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise BadRequest("owner_id must be an integer") from None


def validate_owner(owner_type, owner_id) -> int:
    """Validate an owner type/id pair, returning the parsed owner id.

    An unknown owner type or a missing/non-numeric id is a 400; an id that does
    not exist for that type is a 409.
    """
    if owner_type not in OWNER_TYPES:
        raise BadRequest(f"owner_type must be one of {', '.join(OWNER_TYPES)}")
    parsed = _parse_owner_id(owner_id)
    if db.session.get(_OWNER_MODELS[owner_type], parsed) is None:
        raise Conflict(f"{owner_type} {parsed} does not exist")
    return parsed


def _extension_for(file_storage) -> str:
    """Extension for the stored name, preferring the upload's own file name.

    Device cameras often send an empty filename; fall back to the part's MIME
    type so the stored file still gets a sensible extension.
    """
    name = secure_filename(file_storage.filename or "")
    suffix = Path(name).suffix if name else ""
    if suffix:
        return suffix
    return mimetypes.guess_extension(file_storage.mimetype or "") or ""


def _next_sequence(owner_type: str, day) -> int:
    """One past the highest ``YYYY-MM-DD-SEQ`` already stored for the day."""
    prefix = f"{owner_type}/{day.isoformat()}-"
    paths = (
        db.session.execute(
            db.select(Picture.path).where(Picture.path.like(f"{prefix}%"))
        )
        .scalars()
        .all()
    )
    highest = 0
    for path in paths:
        tail = Path(path).name[len(prefix.split("/", 1)[1]):]
        number = tail.split(".", 1)[0]
        if number.isdigit():
            highest = max(highest, int(number))
    return highest + 1


def store_upload(
    file_storage,
    owner_type,
    owner_id,
    uploaded_by: str | None = None,
) -> Picture:
    """Persist an uploaded file and return its Picture record (uncommitted)."""
    if file_storage is None:
        raise BadRequest("a file field is required")
    owner_id = validate_owner(owner_type, owner_id)

    extension = _extension_for(file_storage)
    day = datetime.now(UTC).date()
    owner_dir = _owner_dir(owner_type)
    uploaded_date = datetime.now(UTC).replace(tzinfo=None)

    for _ in range(_MAX_SEQUENCE_ATTEMPTS):
        stored_name = f"{day.isoformat()}-{_next_sequence(owner_type, day):04d}{extension}"
        stored_path = owner_dir / stored_name
        picture = Picture(
            path=f"{owner_type}/{stored_name}",
            owner_type=owner_type,
            owner_id=owner_id,
            uploaded_by=uploaded_by,
            uploaded_date=uploaded_date,
        )
        db.session.add(picture)
        try:
            # A savepoint lets a name collision roll back the failed insert
            # without discarding the rest of the request's transaction.
            with db.session.begin_nested():
                db.session.flush()
        except IntegrityError:
            db.session.expunge(picture)
            continue
        file_storage.save(stored_path)
        return picture

    raise Conflict("could not allocate a unique picture name; try again")


def resolve_path(picture: Picture) -> Path:
    """Absolute path of a stored picture, under UPLOAD_DIR (validated)."""
    base = Path(current_app.config["UPLOAD_DIR"]).resolve()
    target = (base / picture.path).resolve()
    if not str(target).startswith(str(base) + "/") or not target.is_file():
        raise NotFound(f"file for picture {picture.id} is missing on disk")
    return target


def remove_file(picture: Picture) -> None:
    """Remove a stored picture file from disk (errors are ignored).

    Call this only AFTER the database record deletion has been committed.
    """
    try:
        path = Path(current_app.config["UPLOAD_DIR"]) / picture.path
        if path.is_file():
            path.unlink()
    except OSError:
        pass
