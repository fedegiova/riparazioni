"""API v1 error handlers: consistent ``{"error": "..."}`` JSON envelope."""

from flask import Blueprint, jsonify
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.services.errors import ApiError


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
        return jsonify(error="bad request"), 400
