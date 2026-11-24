"""Owned models: tables the application creates and manages.

Column names follow ``openspec/specs/database_schema.md`` (normalized — see
the change design document for the deltas): explicit VARCHAR lengths,
``REPAIRS.END_DATA``/``REPAIRS.DELIVERY_DATE`` and the work-log
gas-system-state columns required by the field notes, plus the
``REPAIR_PARTS`` join table.

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


def _now() -> datetime:
    """Naive UTC timestamp default (replacement for deprecated datetime.utcnow)."""
    return datetime.now(UTC).replace(tzinfo=None)


def _local_now() -> datetime:
    """Naive local timestamp default for workshop-facing datetimes."""
    return datetime.now().replace(tzinfo=None)


class Refrigerator(db.Model):
    __tablename__ = "REFRIGERATORS"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    serial_nr = db.Column(db.String(32))
    model = db.Column(db.String(32))
    brand = db.Column(db.String(32))
    gas_kg = db.Column(db.Float)
    notes = db.Column(db.String(4000))
    # External reference, no DB FK (see module docstring): validated in the
    # service layer against DATIDBSTORICO.TBALLLESTIMENTI. At most one
    # refrigerator is installed per allestimento (partial unique index below);
    # an uninstalled unit keeps a NULL link.
    allestimento_id = db.Column(db.Integer)
    # Gas type drawn from the configured gas_types setting; must match the
    # selected cylinder for a gas operation.
    gas_kind = db.Column(db.String(32))

    __table_args__ = (
        # One current installation per allestimento. Several uninstalled units
        # are allowed, so the uniqueness is filtered to non-NULL links (SQLite
        # and MSSQL both support the filtered form; MSSQL forbids a plain
        # unique index when many rows are NULL).
        db.Index(
            "uq_refrigerators_allestimento",
            "allestimento_id",
            unique=True,
            sqlite_where=db.text("allestimento_id IS NOT NULL"),
            mssql_where=db.text("allestimento_id IS NOT NULL"),
        ),
    )

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
            "allestimento_id": self.allestimento_id,
            "gas_kind": self.gas_kind,
        }


class GasCylinder(db.Model):
    __tablename__ = "GAS_CYLINDERS"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gas_kind = db.Column(db.String(32))
    serial_nr = db.Column(db.String(32))
    model = db.Column(db.String(32))
    # Required: the archive threshold and every balance computation depend on it.
    full_weight = db.Column(db.Float, nullable=False)
    remaining_weight = db.Column(db.Float)
    notes = db.Column(db.String(4000))
    # Reversible retire flag; an archived cylinder is hidden from the default
    # list and cannot be offered for recharge/recovery until refilled.
    archived = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text("0"))

    # passive_deletes: a cylinder in use by a work-log entry must not be
    # deletable — the DB foreign key rejects it (HTTP 409).
    work_log_entries = db.relationship(
        "RepairWorkLog", back_populates="cylinder", passive_deletes=True
    )
    # Refills are owned by the cylinder: deleting an unreferenced cylinder
    # removes its refill history with it.
    refills = db.relationship(
        "Refill", back_populates="cylinder", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "gas_kind": self.gas_kind,
            "serial_nr": self.serial_nr,
            "model": self.model,
            "full_weight": self.full_weight,
            "remaining_weight": self.remaining_weight,
            "notes": self.notes,
            "archived": self.archived,
        }


class Refill(db.Model):
    """A record that a cylinder was sent out and returned full.

    The amount added is implicit (``full_weight - remaining_weight`` at the
    time of the refill), so only the date and an optional reference are stored.
    """

    __tablename__ = "REFILLS"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gas_cylinder_id = db.Column(
        db.Integer, db.ForeignKey("GAS_CYLINDERS.id"), nullable=False
    )
    date = db.Column(db.Date, nullable=False)
    reference = db.Column(db.String(255))

    cylinder = db.relationship("GasCylinder", back_populates="refills")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "gas_cylinder_id": self.gas_cylinder_id,
            "date": self.date.isoformat() if self.date else None,
            "reference": self.reference,
        }


class ServicePart(db.Model):
    __tablename__ = "SERVICE_PARTS"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    supplier = db.Column(db.String(64))
    kind = db.Column(db.String(64))
    price = db.Column(db.Integer)
    is_refrigerator_part = db.Column(db.Boolean, nullable=False, default=False)
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
            "notes": self.notes,
        }


class Picture(db.Model):
    __tablename__ = "PICTURES"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Relative path under UPLOAD_DIR; the file lives at UPLOAD_DIR / path.
    # Unique: the storage service derives a dated name and retries on collision.
    path = db.Column(db.String(1024), nullable=False, unique=True)
    # Relative path of the minified derivative under UPLOAD_DIR. Null for
    # pictures stored before the derivative existed; the storage service
    # generates it lazily on first read. Unique only among non-null values
    # (a partial index), since several legacy rows may be null.
    thumbnail_path = db.Column(db.String(1024))
    # Exactly one owner: 'repair' | 'spare' | 'cylinder' (validated in the
    # service layer). No junction table — a picture is always attached at upload.
    owner_type = db.Column(db.String(16), nullable=False)
    owner_id = db.Column(db.Integer, nullable=False)
    uploaded_by = db.Column(db.String(64))
    uploaded_date = db.Column(db.DateTime, default=_now)

    __table_args__ = (
        db.Index(
            "uq_pictures_thumbnail_path",
            "thumbnail_path",
            unique=True,
            sqlite_where=db.text("thumbnail_path IS NOT NULL"),
            mssql_where=db.text("thumbnail_path IS NOT NULL"),
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "owner_type": self.owner_type,
            "owner_id": self.owner_id,
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
    start_data = db.Column(db.DateTime, default=_local_now)
    end_data = db.Column(db.DateTime)
    # Delivery date requested by the customer (a date, not a timestamp);
    # distinct from end_data, which is the actual close time.
    delivery_date = db.Column(db.Date)
    notes = db.Column(db.String(4000))
    refrigerator = db.Column(db.Integer, db.ForeignKey("REFRIGERATORS.id"))
    # Set when the repair's first gas operation binds the installed unit, and
    # never cleared: after that the vehicle and refrigerator are frozen so a
    # later replacement cannot silently re-point the repair at another unit.
    gas_equipment_locked = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.text("0")
    )
    # Frozen calendar-adjusted total, written once when the repair is archived.
    # NULL while the repair is active (its total is computed on read) and after
    # a reopen; the service layer reads it instead of recomputing when set.
    archived_total_hours = db.Column(db.Float)

    # Computed on read and attached by the service layer. `total_hours` is the
    # frozen snapshot for an archived repair, else the live adjusted total.
    customer_name = None
    total_hours = 0.0
    gas_used = 0.0
    # Whether the repair's recorded refrigerator is still the one installed on
    # its allestimento (detail reads only): None when no refrigerator is
    # recorded, else True/False.
    refrigerator_installed = None
    # Pictures owned by this repair (owner_type='repair'), attached on read.
    pictures = None

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
            "customer_name": self.customer_name,
            "vehicle": self.vehicle,
            "refrigerator": self.refrigerator,
            "gas_equipment_locked": self.gas_equipment_locked,
            "start_data": self.start_data.isoformat() if self.start_data else None,
            "end_data": self.end_data.isoformat() if self.end_data else None,
            "delivery_date": self.delivery_date.isoformat()
            if self.delivery_date
            else None,
            "total_hours": self.total_hours,
            "gas_used": self.gas_used,
            "notes": self.notes,
        }
        if include_details:
            data["refrigerator_installed"] = self.refrigerator_installed
            data["work_log"] = [entry.to_dict() for entry in self.work_log]
            data["parts"] = [part.to_dict() for part in self.parts]
            data["pictures"] = [picture.to_dict() for picture in (self.pictures or [])]
        return data


class RepairWorkLog(db.Model):
    __tablename__ = "REPAIR_WORK_LOG"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_repairs = db.Column(db.Integer, db.ForeignKey("REPAIRS.id"), nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    operator = db.Column(db.String(32))
    description = db.Column(db.String(4000))
    gas_system_state = db.Column(db.String(16))
    gas_recharge = db.Column(db.Integer, db.ForeignKey("GAS_CYLINDERS.id"))
    gas_recharge_weight = db.Column(db.Float)
    gas_recovered_weight = db.Column(db.Float)
    # Operation discriminator for the gas contract that replaces the state
    # column above: none | fill | recovery | recovery_recharge. NULL on rows
    # written before the change (read as ordinary work). Kept alongside the
    # legacy columns; the service layer stops reading those when the new
    # operation model lands.
    gas_operation = db.Column(db.String(20))
    # The single measured mass in kg: the added amount for fill, the recovered
    # amount for recovery, the net added amount for recovery_recharge.
    gas_measured_kg = db.Column(db.Float)
    # Nameplate capacity used for a combined operation, stored so a later edit
    # of the refrigerator cannot change past calculated recoveries.
    gas_nameplate_kg = db.Column(db.Float)

    repair = db.relationship("Repairs", back_populates="work_log")
    cylinder = db.relationship("GasCylinder", back_populates="work_log_entries")

    def recharged_kg(self):
        """Gross gas recharged by this entry, in kg (None when it moved none).

        A fill recharges exactly what was added; a combined operation recharges
        the whole nameplate (the part not recovered from the unit).
        """
        if self.gas_operation == "fill":
            return self.gas_measured_kg
        if self.gas_operation == "recovery_recharge":
            return self.gas_nameplate_kg
        return None

    def recovered_kg(self):
        """Gas recovered into the cylinder, in kg (None when it moved none).

        A recovery is measured; a combined operation's recovery is calculated
        as nameplate capacity minus the measured net addition.
        """
        if self.gas_operation == "recovery":
            return self.gas_measured_kg
        if self.gas_operation == "recovery_recharge":
            if self.gas_nameplate_kg is None or self.gas_measured_kg is None:
                return None
            return self.gas_nameplate_kg - self.gas_measured_kg
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "operator": self.operator,
            "description": self.description,
            "gas_operation": self.gas_operation,
            "gas_recharge": self.gas_recharge,
            "gas_measured_kg": self.gas_measured_kg,
            "gas_nameplate_kg": self.gas_nameplate_kg,
            "recharged_weight": self.recharged_kg(),
            "recovered_weight": self.recovered_kg(),
        }


class Settings(db.Model):
    """Application settings: a name/value store with JSON-encoded values.

    The value column holds a JSON document as text (see the settings service,
    which validates and (de)serializes it). Unknown names accept any JSON; the
    known settings (``operators``, ``working_hours``, ``holidays``) are
    validated on write.
    """

    __tablename__ = "SETTINGS"

    name = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(4000), nullable=False, default="")

    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value}


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


class TransactionGuard(db.Model):
    """Singleton row serializing repair-lifecycle and timer mutations.

    Every mutating request that could change a repair's archive state or an
    operator's running timer updates row 1 before reading authoritative state.
    The row update makes concurrent writers queue across processes, which a
    process-local mutex cannot do. The row is seeded by the migration and
    created lazily by the service so databases built from the metadata work too.
    """

    __tablename__ = "TRANSACTION_GUARDS"

    # Fixed singleton key (id = 1): not an IDENTITY column, so the row can be
    # inserted explicitly on SQL Server without IDENTITY_INSERT.
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    version = db.Column(db.Integer, nullable=False, default=0)
