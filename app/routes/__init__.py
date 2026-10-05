"""Blueprint registration."""

from flask import Flask

from app.routes.health import bp as health_bp


def register_blueprints(app: Flask) -> None:
    """Attach all feature blueprints to the application."""
    app.register_blueprint(health_bp)
