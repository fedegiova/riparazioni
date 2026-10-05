"""Health-check endpoints for nginx, systemd and monitoring."""

import logging
import time

from flask import Blueprint, jsonify

from app.extensions import db

logger = logging.getLogger(__name__)

bp = Blueprint("health", __name__)


@bp.get("/healthz")
def health():
    """Liveness probe: the web process is running."""
    return jsonify(status="ok", service="riparazioni")


@bp.get("/healthz/db")
def health_database():
    """Readiness probe: the database accepts connections.

    The error detail is only logged server-side; clients get a generic
    response so connection strings are never leaked.
    """
    started = time.monotonic()
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception:  # any DB error means "not ready"
        logger.exception("Database health check failed")
        return jsonify(status="error", database="unreachable"), 503
    latency_ms = round((time.monotonic() - started) * 1000, 2)
    return jsonify(status="ok", database="reachable", latency_ms=latency_ms)
