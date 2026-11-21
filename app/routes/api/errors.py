"""API v1 error handlers: consistent ``{"error": "..."}`` JSON envelope."""

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import ClientDisconnected

from app.extensions import db
from app.services.errors import ApiError


def _request_context() -> str:
    """Request details useful when a 4xx is raised before the view runs."""
    return (
        f"{request.method} {request.path} "
        f"content_type={request.content_type!r} "
        f"content_length={request.content_length!r} "
        f"ua={request.headers.get('User-Agent')!r} "
        f"xff={request.headers.get('X-Forwarded-For')!r} "
        f"remote={request.remote_addr!r}"
    )


def register_error_handlers(bp: Blueprint) -> None:
    """Register app-level JSON error handlers for the API."""

    @bp.app_errorhandler(ApiError)
    def _handle_api_error(error: ApiError):
        return jsonify(error=error.message), error.status_code

    @bp.app_errorhandler(IntegrityError)
    def _handle_integrity_error(error: IntegrityError):
        # Referential-integrity violations surface as HTTP 409.
        db.session.rollback()
        return jsonify(error="conflict with existing data"), 409

    @bp.app_errorhandler(404)
    def _handle_404(error):
        return jsonify(error="not found"), 404

    @bp.app_errorhandler(405)
    def _handle_405(error):
        return jsonify(error="method not allowed"), 405

    @bp.app_errorhandler(400)
    def _handle_400(error):
        # Reached when Flask/Werkzeug rejects the request before a view runs
        # (e.g. a malformed or truncated multipart body). Log the reason so a
        # mobile upload failure is diagnosable instead of a bare "bad request".
        if isinstance(error, ClientDisconnected):
            # The browser closed the connection before sending the full body.
            # This is not a server-side rejection: the upload was aborted
            # client-side (for example, a page reload during the request).
            current_app.logger.warning(
                "client disconnected before the request body was complete: %s",
                _request_context(),
            )
        else:
            current_app.logger.warning(
                "400 %s: %s", _request_context(), getattr(error, "description", error)
            )
        return jsonify(error="bad request"), 400

    @bp.app_errorhandler(413)
    def _handle_413(error):
        current_app.logger.warning(
            "413 %s: %s", _request_context(), getattr(error, "description", error)
        )
        return jsonify(error="request entity too large"), 413
