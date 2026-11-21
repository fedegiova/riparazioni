"""Picture file storage service.

Uploads are decoded as images and stored under
``<UPLOAD_DIR>/<owner_type>/YYYY-MM-DD-SEQ.<ext>``; the ``PICTURES`` row keeps
the path relative to ``UPLOAD_DIR`` (e.g. ``repair/2026-11-21-0007.jpg``). The
stored copy is resized so its longest edge is at most ``MAX_IMAGE_EDGE`` and a
minified derivative (``...YYYY-MM-DD-SEQ.thumb.<ext>``, longest edge at most
``THUMBNAIL_EDGE``) is written beside it for fast grids. ``SEQ`` is a
per-owner-type, per-day sequence zero-padded to four digits; the unique
constraint on ``PICTURES.path`` is the real collision guard, so the sequence is
only a hint and the insert is retried.

Resolving a picture's file location always starts from the stored relative path
joined under ``UPLOAD_DIR`` — client input never reaches the filesystem.
"""

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import GasCylinder, Picture, Repairs, ServicePart
from app.services.errors import BadRequest, Conflict, NotFound

# A picture is always attached to exactly one of these owners (no junction
# table): a repair, a spare (service part), or a gas cylinder.
OWNER_TYPES = ("repair", "spare", "cylinder")
_OWNER_MODELS = {"repair": Repairs, "spare": ServicePart, "cylinder": GasCylinder}
_MAX_SEQUENCE_ATTEMPTS = 5

# Longest edge, in pixels, of the stored image and of its minified derivative.
MAX_IMAGE_EDGE = 2880
THUMBNAIL_EDGE = 320

# Decoded image format -> stored file extension. Anything Pillow can open but
# that is not listed here (or reports no format) falls back to ``.jpg``.
_FORMAT_EXTENSIONS = {
    "JPEG": ".jpg",
    "MPO": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "GIF": ".gif",
    "BMP": ".bmp",
    "TIFF": ".tiff",
}


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


def _load_image(data: bytes) -> tuple[Image.Image, str]:
    """Decode *data* as an image, returning it (orientation applied) and its format.

    A file Pillow cannot decode is a 400. The format is captured before any
    transform because Pillow drops ``Image.format`` on copies/transposes.
    """
    try:
        image = Image.open(BytesIO(data))
        image.load()
        image_format = image.format or "JPEG"
    except (UnidentifiedImageError, OSError, ValueError):
        current_app.logger.warning(
            "picture upload rejected: undecodable image (%d bytes)", len(data)
        )
        raise BadRequest("file must be an image") from None
    return ImageOps.exif_transpose(image), image_format


def _resized(image: Image.Image, edge: int) -> Image.Image:
    """A copy of *image* whose longest edge is at most *edge* (never enlarged)."""
    resized = image.copy()
    resized.thumbnail((edge, edge))
    return resized


def _save_image(image: Image.Image, path: Path, image_format: str) -> None:
    """Write *image* to *path*, preserving its format (JPEG needs a flat mode)."""
    save_format = "JPEG" if image_format == "MPO" else image_format
    to_save = image
    if save_format == "JPEG" and image.mode not in ("RGB", "L"):
        to_save = image.convert("RGB")
    to_save.save(path, format=save_format)


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
    """Persist an uploaded image and return its Picture record (uncommitted).

    The upload is decoded and resized to ``MAX_IMAGE_EDGE``; a minified
    derivative at ``THUMBNAIL_EDGE`` is written alongside it. A file that is not
    a decodable image is a 400 and stores nothing.
    """
    if file_storage is None:
        current_app.logger.warning("picture upload rejected: no file part")
        raise BadRequest("a file field is required")
    owner_id = validate_owner(owner_type, owner_id)

    data = file_storage.read()
    if not data:
        current_app.logger.warning(
            "picture upload rejected: empty file part (filename=%r, mimetype=%r)",
            file_storage.filename,
            file_storage.mimetype,
        )
        raise BadRequest("a file field is required")
    image, image_format = _load_image(data)
    extension = _FORMAT_EXTENSIONS.get(image_format, ".jpg")
    full = _resized(image, MAX_IMAGE_EDGE)
    thumbnail = _resized(image, THUMBNAIL_EDGE)

    day = datetime.now(UTC).date()
    owner_dir = _owner_dir(owner_type)
    uploaded_date = datetime.now(UTC).replace(tzinfo=None)

    for _ in range(_MAX_SEQUENCE_ATTEMPTS):
        sequence = _next_sequence(owner_type, day)
        stored_name = f"{day.isoformat()}-{sequence:04d}{extension}"
        thumbnail_name = f"{day.isoformat()}-{sequence:04d}.thumb{extension}"
        picture = Picture(
            path=f"{owner_type}/{stored_name}",
            thumbnail_path=f"{owner_type}/{thumbnail_name}",
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
        _save_image(full, owner_dir / stored_name, image_format)
        _save_image(thumbnail, owner_dir / thumbnail_name, image_format)
        return picture

    raise Conflict("could not allocate a unique picture name; try again")


def _safe_path(relative: str | None) -> Path | None:
    """Absolute path under UPLOAD_DIR for *relative*, or None when unusable."""
    if not relative:
        return None
    base = Path(current_app.config["UPLOAD_DIR"]).resolve()
    target = (base / relative).resolve()
    if not str(target).startswith(str(base) + "/") or not target.is_file():
        return None
    return target


def resolve_path(picture: Picture) -> Path:
    """Absolute path of a stored picture, under UPLOAD_DIR (validated)."""
    target = _safe_path(picture.path)
    if target is None:
        raise NotFound(f"file for picture {picture.id} is missing on disk")
    return target


def generate_thumbnail(picture: Picture) -> Path:
    """Derive the minified view from the stored file and record it.

    Used for pictures stored before this feature existed (or whose derivative
    went missing); commits the recorded ``thumbnail_path``.
    """
    source = resolve_path(picture)
    image, image_format = _load_image(source.read_bytes())
    extension = _FORMAT_EXTENSIONS.get(image_format, ".jpg")
    stored = Path(picture.path)
    thumbnail_rel = f"{stored.parent.as_posix()}/{stored.stem}.thumb{extension}"
    target = Path(current_app.config["UPLOAD_DIR"]) / thumbnail_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    _save_image(_resized(image, THUMBNAIL_EDGE), target, image_format)
    picture.thumbnail_path = thumbnail_rel
    db.session.commit()
    return target


def resolve_thumbnail_path(picture: Picture) -> Path:
    """Absolute path of the minified view, generating it lazily when missing."""
    target = _safe_path(picture.thumbnail_path)
    if target is not None:
        return target
    return generate_thumbnail(picture)


def remove_file(picture: Picture) -> None:
    """Remove a stored picture and its derivative from disk (errors ignored).

    Call this only AFTER the database record deletion has been committed.
    """
    for relative in (picture.path, picture.thumbnail_path):
        if not relative:
            continue
        try:
            path = Path(current_app.config["UPLOAD_DIR"]) / relative
            if path.is_file():
                path.unlink()
        except OSError:
            pass
