"""Owned models: tables the application creates and manages.

Column names follow ``openspec/specs/database_schema.md`` (normalized — see
the change design document for the deltas): explicit VARCHAR lengths,
``REPAIRS.END_DATA``/``REPAIRS.TYPE`` and the work-log gas-system-state
columns required by the field notes, plus the ``REPAIR_PARTS`` join table.

Owned tables use lowercase column names (``id``, ``customer``, ...). The
read-only external tables in ``DATIDBSTORICO`` keep their documented
UPPERCASE names.

``REPAIRS.customer`` and ``REPAIRS.vehicle`` reference the external legacy
objects (``VICLIENTI`` view, ``TBALLESTIMENTI`` table) but carry NO database
foreign-key constraints: the migration only creates owned tables, and MSSQL
cannot create an FK to a view anyway. Referential integrity for both is
validated in the service layer (HTTP 409 when the id does not exist).
"""

from datetime import UTC, datetime

from app.extensions import db

REPAIR_TYPES = ("RIPA", "RIPA_FRIGO")
GAS_SYSTEM_STATES = ("VUOTO", "PIENO", "RICUPERO_RICARICA")


def _now() -> datetime:
    """Naive UTC timestamp default (replacement for deprecated datetime.utcnow)."""
    return datetime.now(UTC).replace(tzinfo=None)


class Refrigerator(db.Model):
    __tablename__ = "REFRIGERATORS"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    serial_nr = db.Column(db.String(32))
    model = db.Column(db.String(32))
    brand = db.Column(db.String(32))
    gas_kg = db.Column(db.Float)
    notes = db.Column(db.String(4000))

    # passive_deletes: do not NULL out referencing repairs on delete — let the
    # DB foreign key reject the delete (surfaced as HTTP 409).
    repairs = db.relationship(
        "Repairs", back_populates="refrigerator_rel", passive_deletes=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "serial_nr": self.serial_nr,
            "model": self.model,
            "brand": self.brand,
            "gas_kg": self.gas_kg,
            "notes": self.notes,
        }


class GasCylinder(db.Model):
    __tablename__ = "GAS_CYLINDERS"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gas_kind = db.Column(db.String(32))
    serial_nr = db.Column(db.String(32))
    model = db.Column(db.String(32))
    full_weight = db.Column(db.Float)
    remaining_weight = db.Column(db.Float)
    picture_ref = db.Column(db.Integer, db.ForeignKey("PICTURES.id"))
    notes = db.Column(db.String(4000))

    # passive_deletes: a cylinder in use by a work-log entry must not be
    # deletable — the DB foreign key rejects it (HTTP 409).
    work_log_entries = db.relationship(
        "RepairWorkLog", back_populates="cylinder", passive_deletes=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "gas_kind": self.gas_kind,
            "serial_nr": self.serial_nr,
            "model": self.model,
            "full_weight": self.full_weight,
            "remaining_weight": self.remaining_weight,
            "picture_ref": self.picture_ref,
            "notes": self.notes,
        }


class ServicePart(db.Model):
    __tablename__ = "SERVICE_PARTS"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    supplier = db.Column(db.String(64))
    kind = db.Column(db.String(64))
    price = db.Column(db.Integer)
    is_refrigerator_part = db.Column(db.Boolean, nullable=False, default=False)
    picture_ref = db.Column(db.Integer, db.ForeignKey("PICTURES.id"))
    notes = db.Column(db.String(4000))

    # passive_deletes: a part used by a repair must not be deletable — the DB
    # foreign key rejects it (HTTP 409).
    repair_parts = db.relationship(
        "RepairPart", back_populates="part", passive_deletes=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "supplier": self.supplier,
            "kind": self.kind,
            "price": self.price,
            "is_refrigerator_part": self.is_refrigerator_part,
            "picture_ref": self.picture_ref,
            "notes": self.notes,
        }


class Picture(db.Model):
    __tablename__ = "PICTURES"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Relative path under UPLOAD_DIR; the file lives at UPLOAD_DIR / path.
    path = db.Column(db.String(1024), nullable=False)
    uploaded_by = db.Column(db.String(64))
    uploaded_date = db.Column(db.DateTime, default=_now)

    # passive_deletes: referenced pictures must not be deletable — the DB
    # foreign keys reject it (HTTP 409).
    cylinders = db.relationship(
        "GasCylinder",
        foreign_keys="GasCylinder.picture_ref",
        passive_deletes=True,
    )
    parts = db.relationship(
        "ServicePart",
        foreign_keys="ServicePart.picture_ref",
        passive_deletes=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "uploaded_by": self.uploaded_by,
            "uploaded_date": self.uploaded_date.isoformat() if self.uploaded_date else None,
        }


class Repairs(db.Model):
    __tablename__ = "REPAIRS"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # External reference, no DB FK (see module docstring): validated in the
    # service layer against DATIDBSTORICO.VICLIENTI.
    customer = db.Column(db.Integer)
    # External reference, no DB FK (see module docstring): validated in the
    # service layer against DATIDBSTORICO.TBALLLESTIMENTI.
    vehicle = db.Column(db.Integer)
    start_data = db.Column(db.DateTime, default=_now)
    end_data = db.Column(db.DateTime)
    type = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.String(4000))
    refrigerator = db.Column(db.Integer, db.ForeignKey("REFRIGERATORS.id"))

    refrigerator_rel = db.relationship("Refrigerator", back_populates="repairs")
    work_log = db.relationship(
        "RepairWorkLog",
        back_populates="repair",
        cascade="all, delete-orphan",
    )
    parts = db.relationship(
        "RepairPart",
        back_populates="repair",
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_details: bool = False) -> dict:
        data = {
            "id": self.id,
            "customer": self.customer,
            "vehicle": self.vehicle,
            "type": self.type,
            "refrigerator": self.refrigerator,
            "start_data": self.start_data.isoformat() if self.start_data else None,
            "end_data": self.end_data.isoformat() if self.end_data else None,
            "notes": self.notes,
        }
        if include_details:
            data["work_log"] = [entry.to_dict() for entry in self.work_log]
            data["parts"] = [part.to_dict() for part in self.parts]
        return data


class RepairWorkLog(db.Model):
    __tablename__ = "REPAIR_WORK_LOG"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_repairs = db.Column(db.Integer, db.ForeignKey("REPAIRS.id"), nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    operator = db.Column(db.String(32))
    gas_system_state = db.Column(db.String(16))
    gas_recharge = db.Column(db.Integer, db.ForeignKey("GAS_CYLINDERS.id"))
    gas_recharge_weight = db.Column(db.Float)
    gas_recovered_weight = db.Column(db.Float)

    repair = db.relationship("Repairs", back_populates="work_log")
    cylinder = db.relationship("GasCylinder", back_populates="work_log_entries")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "operator": self.operator,
            "gas_system_state": self.gas_system_state,
            "gas_recharge": self.gas_recharge,
            "gas_recharge_weight": self.gas_recharge_weight,
            "gas_recovered_weight": self.gas_recovered_weight,
        }


class RepairPart(db.Model):
    __tablename__ = "REPAIR_PARTS"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_repairs = db.Column(db.Integer, db.ForeignKey("REPAIRS.id"), nullable=False)
    id_part = db.Column(db.Integer, db.ForeignKey("SERVICE_PARTS.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer)

    repair = db.relationship("Repairs", back_populates="parts")
    part = db.relationship("ServicePart", back_populates="repair_parts")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_part": self.id_part,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "part": self.part.to_dict() if self.part else None,
        }
