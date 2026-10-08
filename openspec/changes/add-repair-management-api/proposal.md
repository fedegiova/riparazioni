# Proposal

## Why

The scaffolded Flask app can reach the MSSQL database but has no domain
functionality. The business needs a backend that manages the repair
workflow (RIPA and RIPA FRIGO repairs, work log, gas recharges), its own
master data (refrigerators, gas cylinders, service parts), and repair
photos — while reading legacy master data (vehicles, customers, users)
that already lives in the `DATIDBSTORICO` schema.

## What Changes

- Add SQLAlchemy models for the application-owned tables (`REPAIRS`,
  `REPAIR_WORK_LOG`, `REFRIGERATORS`, `GAS_CYLINDERS`, `SERVICE_PARTS`,
  `PICTURES`), normalized from `openspec/specs/database_schema.md` (the DDL
  in that doc is pseudo-SQL; normalization details, including fields its own
  notes require and a `REPAIR_PARTS` association table, are in design.md).
- Add an initial Alembic migration creating the owned tables. The three
  pre-existing `DATIDBSTORICO` objects are mapped read-only and are NOT
  migrated.
- Add a versioned JSON REST API under `/api/v1`:
  - Full CRUD: `repairs`, `refrigerators`, `gas-cylinders`, `service-parts`
  - Nested work-log CRUD under a repair, with gas-recharge handling that
    updates the cylinder's remaining weight
  - `pictures`: multipart upload (file stored under `UPLOAD_DIR`), list,
    detail, download, delete
  - Read-only list/detail: `vehicles`, `customers`, `users` (user password
    is never exposed)
- Consistent JSON error responses (400/404/405/409) for validation,
  unknown IDs, writes to read-only resources, and integrity violations.

## Capabilities

### New Capabilities

- `repairs`: creation and lifecycle of repair records (RIPA / RIPA FRIGO
  types), work-log entries, used parts, and gas-recharge operations that
  keep cylinder balances current.
- `equipment`: CRUD management of owned master data — refrigerators, gas
  cylinders, service parts.
- `reference-data`: read-only access to pre-existing external tables
  (vehicles, customers, users) in the `DATIDBSTORICO` schema; no writes,
  no password exposure.
- `pictures`: storing and serving photo files on the local filesystem
  (upload, list, detail, download, delete) with metadata in the `PICTURES`
  table.

### Modified Capabilities

(none — no capability specs exist yet)

## Impact

- **Code**: new models in `app/models/`, new `api` blueprint in
  `app/routes/api/`, business logic in `app/services/`; blueprint registered
  in `app/routes`. Health endpoints and app factory unchanged.
- **Database**: one initial migration creating seven tables (the six owned
  tables plus `REPAIR_PARTS`); no changes to `DATIDBSTORICO` objects.
  Applying it requires a reachable MSSQL database.
- **Filesystem**: picture files written under `UPLOAD_DIR/pictures`
  (existing `UPLOAD_DIR` config; directories already created at startup).
- **Dependencies**: none new (Flask multipart handling and
  `werkzeug.utils.secure_filename` are sufficient).
- **Testing**: new model/API tests, all runnable without a live MSSQL
  server (SQLite in-memory with faked external tables — see design.md).
