"""Read-only models for pre-existing objects in the DATIDBSTORICO schema.

These objects are owned by the legacy system (see
``openspec/specs/external_tables.md``). They are mapped with explicit
``Table`` objects — no migration ever creates or alters them — and the API
only exposes read endpoints. Column types follow the documented DDL; a
smoke check against the live database must reconcile them (see task 1.5).
"""

from app.extensions import db


def _table(name: str, *columns) -> db.Table:
    """Table in the DATIDBSTORICO schema, on the app metadata."""
    return db.Table(name, db.metadata, *columns, schema="DATIDBSTORICO")


_vehicle_table = _table(
    "TBALLESTIMENTI",
    db.Column("ID_INT", db.Integer, primary_key=True),
    db.Column("ID", db.String(15)),
    db.Column("NOMINATIVO_ID", db.String(15), nullable=False),
    db.Column("TARGA", db.String(9)),
    db.Column("AUTOCARRO", db.String(25)),
    db.Column("CARROZZERIA", db.String(20)),
    db.Column("MODELLO", db.String(10)),
    db.Column("CLASSE", db.String(7)),
    db.Column("COMMESSA", db.String(10)),
    db.Column("PROD", db.Date),
    db.Column("ATP", db.Date),
    db.Column("PROGRESSIVO", db.Integer),
    db.Column("DATA_RILASCIO", db.Date),
    db.Column("OL", db.String(20)),
    db.Column("NOTE", db.String(4000)),
    db.Column("CPCCCHK", db.String(10)),
)

_customer_table = _table(
    "VICLIENTI",
    db.Column("ID", db.Integer, primary_key=True),
    db.Column("N_NOMINATIVO", db.Integer),
    db.Column("CLIENTE", db.String(100)),
    db.Column("NCLIENTE", db.String(10)),
    db.Column("VIA", db.String(100)),
    db.Column("CAP", db.String(10)),
    db.Column("CITTA", db.String(50)),
    db.Column("PROV", db.String(3)),
    db.Column("TEL", db.String(20)),
    db.Column("FAX", db.String(20)),
    db.Column("CELL", db.String(20)),
    db.Column("EMAIL", db.String(100)),
    db.Column("NOTE", db.String(4000)),
)

_user_table = _table(
    "TBUSERS",
    db.Column("ID_INT", db.Integer, primary_key=True),
    db.Column("ID", db.String(15)),
    db.Column("NAME", db.String(20), nullable=False),
    db.Column("PASSWORD", db.String(40), nullable=False),
    db.Column("LAST_LOGIN", db.Date),
)


class Vehicle(db.Model):
    """Pre-existing vehicle table (legacy system). Read-only."""

    __tablename__ = "TBALLESTIMENTI"
    __table__ = _vehicle_table

    def to_dict(self) -> dict:
        return {
            "id": self.ID_INT,
            "id_str": self.ID,
            "nominativo_id": self.NOMINATIVO_ID,
            "targa": self.TARGA,
            "autocarro": self.AUTOCARRO,
            "carrozzeria": self.CARROZZERIA,
            "modello": self.MODELLO,
            "classe": self.CLASSE,
            "commessa": self.COMMESSA,
            "prod": self.PROD.isoformat() if self.PROD else None,
            "atp": self.ATP.isoformat() if self.ATP else None,
            "progressivo": self.PROGRESSIVO,
            "data_rilascio": self.DATA_RILASCIO.isoformat() if self.DATA_RILASCIO else None,
            "ol": self.OL,
            "note": self.NOTE,
            "cpccchk": self.CPCCCHK,
        }


class Customer(db.Model):
    """Pre-existing customer view (legacy system). Read-only."""

    __tablename__ = "VICLIENTI"
    __table__ = _customer_table

    def to_dict(self) -> dict:
        return {
            "id": self.ID,
            "n_nominativo": self.N_NOMINATIVO,
            "cliente": self.CLIENTE,
            "ncliente": self.NCLIENTE,
            "via": self.VIA,
            "cap": self.CAP,
            "citta": self.CITTA,
            "prov": self.PROV,
            "tel": self.TEL,
            "fax": self.FAX,
            "cell": self.CELL,
            "email": self.EMAIL,
            "note": self.NOTE,
        }


class AppUser(db.Model):
    """Pre-existing user table (legacy system). Read-only.

    The PASSWORD column is mapped (needed for the table definition) but is
    NEVER included in API responses.
    """

    __tablename__ = "TBUSERS"
    __table__ = _user_table

    def to_dict(self) -> dict:
        return {
            "id": self.ID_INT,
            "id_str": self.ID,
            "name": self.NAME,
            "last_login": self.LAST_LOGIN.isoformat() if self.LAST_LOGIN else None,
        }
