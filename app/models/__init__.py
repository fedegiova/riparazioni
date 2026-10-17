"""SQLAlchemy models.

Owned tables (created by this application's migrations) and read-only
mappings of the pre-existing ``DATIDBSTORICO`` objects. Re-exported so
that Alembic autogenerate detects owned models, while external tables are
explicitly excluded from migrations (see app/models/external.py).
"""

from app.models.external import AppUser, Customer, Vehicle
from app.models.owned import (
    GAS_SYSTEM_STATES,
    REPAIR_TYPES,
    GasCylinder,
    Picture,
    Refrigerator,
    RepairPart,
    Repairs,
    RepairWorkLog,
    ServicePart,
)

__all__ = [
    "GAS_SYSTEM_STATES",
    "REPAIR_TYPES",
    "AppUser",
    "Customer",
    "GasCylinder",
    "Picture",
    "Refrigerator",
    "RepairPart",
    "RepairWorkLog",
    "Repairs",
    "ServicePart",
    "Vehicle",
]
