"""Shared extension instances.

Created in their own module to avoid circular imports between the
application factory and the modules that use them (models, routes, ...).
"""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
