# Design

## Context

The Flask scaffold exists: app factory, SQLAlchemy + Flask-Migrate
initialized, `DATABASE_URL` (mssql+pyodbc, ODBC Driver 18),
`UPLOAD_DIR`/`LOG_DIR` config with startup directory creation, and health
endpoints. Two reference documents define the data:
`openspec/specs/database_schema.md` (owned tables + Italian field notes)
and `openspec/specs/external_tables.md` (pre-existing
`DATIDBSTORICO` objects). The legacy system owns that schema; this app
must reference it read-only. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- ORM models for owned and external tables; one initial migration for the
  owned tables only
- JSON REST API under `/api/v1` covering the four capabilities
  (`repairs`, `equipment`, `reference-data`, `pictures`)
- Picture file storage under `UPLOAD_DIR`
- A test suite that runs without a live MSSQL server

**Non-Goals:**
- Authentication/authorization (TBUSERS is read-only reference; no login)
- Frontend, pagination, reporting/invoicing
- Any write to `DATIDBSTORICO` objects

## Decisions

1. **External tables as `Table`-based mapped classes in schema
   `DATIDBSTORICO`** (read-only, no migrations, no write endpoints).
   `Customer` maps the `VICLIENTI` view; `AppUser` maps `TBUSERS` but its
   serializer omits `PASSWORD`. Alternative — raw SQL queries — rejected:
   ORM mapping keeps the API layer uniform and lets owned models declare
   real FK relationships to the external tables.
2. **Normalize the pseudo-SQL in database_schema.md.** The doc contains
   syntax errors (`CONSTRAIN`, bare `VARCHAR`, an FK to `INT_ID` where the
   real column is `ID_INT`) and omits fields its own notes require:
   - `REPAIRS`: add `END_DATA DATETIME NULL` (note: "ora e data fine") and
     `TYPE CHAR(10) NOT NULL` constrained to `RIPA`/`RIPA_FRIGO` (the notes
     define two repair kinds).
   - `REPAIR_WORK_LOG`: add `GAS_SYSTEM_STATE CHAR(16) NULL`
     (`VUOTO`/`PIENO`/`RICUPERO_RICARICA`) and `GAS_RECOVERED_WEIGHT FLOAT
     NULL` (the toggle notes need both recovered and recharged weights; the
     DDL has one weight column).
   - Add `REPAIR_PARTS` join table (`ID`, `ID_REPAIRS` FK, `ID_PART` FK,
     `QUANTITY INT NOT NULL`, `UNIT_PRICE INT NULL`) — the notes list
     "ricambi" as a repair field but the DDL has no association table.
   - All `VARCHAR`s get explicit lengths (4000 for notes).
3. **Hand-rolled REST endpoints** in a new `api` blueprint
   (`app/routes/api/`), business rules in `app/services/`, simple
   per-model `to_dict()` serialization. Alternative — flask-smorest/
   apispec — rejected for now: it adds a dependency and an OpenAPI surface
   before any consumer needs it; revisit when a frontend contract is
   required.
4. **Cylinder balance updates in the service layer, same DB transaction as
   the work-log entry insert/delete** (atomic; delete restores the balance).
   Recovery (`RICUPERO_RICARICA`) records the recovered kg but does NOT
   credit any cylinder balance — the notes only require recording it.
5. **Picture files stored as `UPLOAD_DIR/pictures/<uuid4-hex><ext>`**;
   `PICTURES.PATH` holds the path relative to `UPLOAD_DIR`. Downloads
   resolve only the stored relative path under `UPLOAD_DIR` — client input
   never reaches the filesystem, so path traversal is impossible by
   construction. Generated names mean no collision handling.
6. **JSON error envelope `{"error": "..."}`** with 400 (validation),
   404 (unknown ID / missing file), 405 (writes to read-only resources),
   409 (FK violations, mapped from `SQLAlchemyIntegrityError`).
7. **Tests on in-memory SQLite with an attached `DATIDBSTORICO`
   database**: a `connect` event listener runs `ATTACH DATABASE
   ':memory:' AS DATIDBSTORICO` so the external tables'
   `schema="DATIDBSTORICO"` mappings resolve to real tables (SQLite
   supports attached databases as schema names — no statement rewriting
   needed), and `PRAGMA foreign_keys=ON` so FK→409 scenarios behave like
   MSSQL for same-database FKs. Caveat: SQLite does not enforce FKs that
   cross attached databases, so the owned→external FKs (customer,
   vehicle) are validated in the service layer — which is also how they
   are enforced in production (MSSQL forbids FKs to views). The
   MSSQL-specific surface (ODBC driver, real legacy tables) is covered by
   a manual smoke task, not the unit suite.

## Risks / Trade-offs

- [SQLite/MSSQL semantic drift] → identical ORM code paths in tests; a
  manual MSSQL smoke task (migration + one endpoint per group) precedes
  deployment.
- [Documented DDL may not match the real legacy tables] → models map the
  documented columns; task group 1 includes a smoke check of the external
  tables against a live DB and fixes model mismatches there (never in the
  migration, which must not touch `DATIDBSTORICO`).
- [Concurrent recharges could overdraw a cylinder] → check-and-update in a
  single short transaction; acceptable at this scale (no extra locking).
- [Repair delete cascades to work log and parts] →
  `cascade="all, delete-orphan"` on the relationships; covered by a test.

## Migration Plan

- One initial Alembic revision creates `REPAIRS`, `REPAIR_WORK_LOG`,
  `REPAIR_PARTS`, `REFRIGERATORS`, `GAS_CYLINDERS`, `SERVICE_PARTS`,
  `PICTURES` in the default schema; downgrade drops them in reverse order.
- Deploy: run `flask db upgrade` before enabling the new code. Rollback:
  `flask db downgrade -1` — the tables are new, so no data loss.

## Open Questions

(None — ambiguities in the reference docs are resolved by the recorded
normalizations above.)
