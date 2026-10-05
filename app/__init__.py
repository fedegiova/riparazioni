"""Application package.

Usage::

    from app import create_app
    app = create_app()
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

# Load .env *before* the config module reads environment variables.
load_dotenv()

from app import config as config_module
from app.extensions import db, migrate
from app.routes import register_blueprints

CONFIGS = {
    "development": config_module.DevelopmentConfig,
    "testing": config_module.TestingConfig,
    "production": config_module.ProductionConfig,
}


def create_app(config_name: str | None = None) -> Flask:
    """Build and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")
    try:
        config_obj = CONFIGS[config_name]
    except KeyError:
        raise ValueError(f"Unknown configuration: {config_name!r}") from None

    app = Flask(__name__)
    app.config.from_object(config_obj)

    db.init_app(app)
    migrate.init_app(app, db)
    register_blueprints(app)

    if not app.testing:
        _ensure_var_directories(app)
    _configure_logging(app)

    return app


def _ensure_var_directories(app: Flask) -> None:
    """Create the writable runtime directories (uploads, logs)."""
    for key in ("UPLOAD_DIR", "LOG_DIR"):
        path = Path(app.config[key])
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            app.logger.warning("%s (%s) could not be created: %s", key, path, exc)


def _configure_logging(app: Flask) -> None:
    """Log to the console, and to a file under LOG_DIR when available."""
    level = logging.DEBUG if app.debug else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if not app.testing:
        log_dir = Path(app.config["LOG_DIR"])
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_dir / "app.log"))
        except OSError:
            pass  # fall back to console-only logging
    formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    for handler in handlers:
        handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = handlers
