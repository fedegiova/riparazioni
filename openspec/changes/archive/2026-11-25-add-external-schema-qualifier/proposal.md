# Proposal

## Why

On SQL Server the legacy `DATIDBSTORICO` schema is nested inside the
`AHR_GIOPLAST` database, while the app's owned tables live in the database
named by `DATABASE_URL`. The read-only external models hard-code the bare
`DATIDBSTORICO` schema, so against SQL Server they compile to
`DATIDBSTORICO.TBALLESTIMENTI` and friends and fail (or resolve in the wrong
database). They only work as written against the SQLite dev/test database,
which is literally attached under that name.

## What Changes

- Introduce an `EXTERNAL_DB_SCHEMA` setting that qualifies the legacy
  reference objects. Default `DATIDBSTORICO` (dev mode / tests); on SQL Server
  set the cross-database 3-part name `AHR_GIOPLAST.DATIDBSTORICO`.
- Route the external `Table` mappings, the Alembic exclusion filter for the
  external objects, and the dev-mode SQLite `ATTACH`/DDL through that one
  setting, so production and dev stay consistent.
- Dev mode keeps the bare attached schema name and fails fast with a clear
  message when a cross-database 3-part qualifier is configured (SQLite attaches
  a single file under one name).
- No API contract change: same endpoints, response shapes, and status codes on
  both databases.

## Capabilities

### New Capabilities
<!-- None: this qualifies existing reference-data behavior rather than
     introducing a new capability. -->

### Modified Capabilities
- `reference-data`: reference objects are resolved through a configurable
  legacy-schema qualifier, enabling the SQL Server cross-database
  (`AHR_GIOPLAST.DATIDBSTORICO`) 3-part name while dev and tests keep the bare
  `DATIDBSTORICO`.
- `dev-mode`: dev mode attaches the external SQLite database under the
  configured schema name and rejects a cross-database qualifier that cannot be
  represented locally.

## Impact

- Backend: `app/config.py` (new setting), `app/models/external.py` (external
  table mappings), `migrations/env.py` (external-object exclusion filter),
  `app/dev_db.py` (SQLite attach and external DDL).
- Config/docs: `.env.example`, `README.md`.
- Tests: `tests/test_models.py` regression asserting the SQL Server 3-part
  rendering.
- Database support: no schema or Alembic migration change; the setting only
  changes how the pre-existing external objects are qualified. Dev mode and the
  SQLite test suite are unaffected by the default.
