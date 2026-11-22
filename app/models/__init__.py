"""SQLAlchemy models.

Owned tables (created by this application's migrations) and read-only
mappings of the pre-existing ``DATIDBSTORICO`` objects. Re-exported so
that Alembic autogenerate detects owned models, while external tables are
explicitly excluded from migrations (see app/models/external.py).
"""

from app.models.external import AppUser, Customer, Vehicle
from app.models.owned import (
    GasCylinder,
    Picture,
    Refill,
    Refrigerator,
    RepairPart,
    Repairs,
    RepairWorkLog,
    ServicePart,
    Settings,
    TransactionGuard,
)

__all__ = [
    "AppUser",
    "Customer",
    "GasCylinder",
    "Picture",
    "Refill",
    "Refrigerator",
    "RepairPart",
    "RepairWorkLog",
    "Repairs",
    "ServicePart",
    "Settings",
    "TransactionGuard",
    "Vehicle",
]
