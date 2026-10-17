"""API v1 blueprint: JSON REST endpoints under /api/v1.

Route modules are imported at the bottom so they can register their
endpoints on ``bp``; the error handlers run last so every error (including
IntegrityError raised deep in the service layer) renders as JSON.
"""

from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api/v1")

from app.routes.api import equipment, pictures, reference, repairs  # noqa: F401
from app.routes.api.errors import register_error_handlers

register_error_handlers(bp)
