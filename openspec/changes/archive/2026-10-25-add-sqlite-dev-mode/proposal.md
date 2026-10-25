# Proposal

## Why

Developing this app currently requires a reachable MSSQL server with ODBC
Driver 18 installed and a migrated database, plus a legacy `DATIDBSTORICO`
schema (vehicles, customers, users) owned by another system that a developer
may not have access to at all. A local, self-contained dev mode — SQLite
backend with the external tables created and pre-seeded — removes every
external prerequisite so `make dev` works on a fresh machine with zero
setup.

## What Changes

- Add an explicit, opt-in **dev mode** switch: the `DEV_MODE=1` environment
  variable (honored in the development config only; production and testing
  configs are untouched). When on, the app's `SQLALCHEMY_DATABASE_URI`
  defaults to a local SQLite file (`var/dev.sqlite3`, overridable with
  `DEV_DATABASE_URL`) and every SQLite connection `ATTACH`es a second file
  (`var/dev_external.sqlite3`) as the `DATIDBSTORICO` schema, mirroring the
  existing test-suite shim in `tests/conftest.py`.
- Add a `flask dev-init` CLI command (idempotent) that prepares the dev
  databases: applies the Alembic migrations to the owned tables, creates the
  three external `DATIDBSTORICO` tables if missing, and seeds them with
  prebaked data when they are empty. A `--reset` flag wipes and recreates
  everything (owned tables back to an empty migrated state, external tables
  re-seeded).
- Add prebaked dev seed data for the external tables, derived from the
  `clienti.sql` sample (one customer, one vehicle, one user), stored as a
  committed, editable SQLite-dialect SQL file; developers can point
  `DEV_SEED_SQL` at their own seed file instead.
- Add a `make dev` target that runs `dev-init` and then the Flask dev server
  with `DEV_MODE=1`; document dev mode (enabling, resetting, customizing
  seed data) in the README and `.env.example`.

Out of scope: any change to the `/api/v1` contract or behavior (dev mode is
transparent to the API), seeding owned tables (refrigerators, cylinders,
parts, repairs start empty and are created via the API), auto-initializing
the database at app startup (setup is an explicit step), and any production
deployment changes.

## Capabilities

### New Capabilities

- `dev-mode`: the local development environment without MSSQL — the opt-in
  switch, the SQLite database layout (owned + attached `DATIDBSTORICO`),
  the explicit `dev-init` setup/reset command, prebaked and customizable
  external reference data, and the `make dev` workflow.

### Modified Capabilities

(none — the reference-data, repairs, equipment and pictures requirements are
unchanged; dev mode only changes which database backs them in development)

## Impact

- **New code**: `app/dev_db.py` (dev-mode config resolution, `ATTACH`
  listener, `dev-init` logic), a new `flask dev-init` CLI command registered
  in `app/__init__.py`, a new `dev/` directory with the prebaked seed file.
- **Modified code**: `app/config.py` (dev-mode settings in
  `DevelopmentConfig`), `Makefile` (`dev` / `dev-init` targets),
  `.env.example`, `README.md`.
- **New tests**: `tests/test_dev_mode.py` covering config resolution,
  dev-init create/seed/idempotency/reset, custom seed files, and API reads
  served from the dev databases.
- **No changes** to `migrations/` (the owned-table migrations and the
  `DATIDBSTORICO` exclusion filter are reused as-is), to the API contract /
  `docs/openapi.yaml`, to `app/models/`, `app/services/`, or `app/routes/`,
  and to production deployment. No new runtime dependencies (the SQLite
  driver ships with Python; the test suite already runs on SQLite).
