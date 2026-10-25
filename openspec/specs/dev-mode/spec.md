# dev-mode Specification

## Purpose

A self-contained local development environment for the repair-management
backend: with an explicit opt-in, the app runs against local SQLite files
instead of MSSQL, with the legacy `DATIDBSTORICO` reference tables created
and pre-seeded, so development needs no external database at all.

## Requirements

### Requirement: Dev mode is an explicit opt-in

Dev mode SHALL be enabled only by an explicit switch (the `DEV_MODE`
environment variable set to a truthy value) and SHALL be honored only in the
development environment. With the switch off (the default), development
behavior is unchanged: the configured MSSQL `DATABASE_URL` is used.
Production and testing environments SHALL ignore the switch entirely.
Running in dev mode SHALL NOT require a reachable MSSQL server or the ODBC
driver.

#### Scenario: Switch off keeps the current behavior

- **WHEN** the app starts in the development environment without `DEV_MODE` set
- **THEN** the database configuration is identical to today's (the MSSQL `DATABASE_URL`) and no dev-mode behavior applies

#### Scenario: Switch on selects the local dev databases

- **WHEN** the app starts in the development environment with `DEV_MODE` set to a truthy value
- **THEN** the application database is the local SQLite dev database instead of `DATABASE_URL`, with no MSSQL server or ODBC driver required

#### Scenario: Other environments ignore the switch

- **WHEN** `DEV_MODE` is set to a truthy value but the app runs in the production or testing environment
- **THEN** dev mode is not active and that environment's own database configuration applies unchanged

### Requirement: Local SQLite dev database layout

In dev mode the backend SHALL run against local SQLite files under the
runtime directory: the owned application tables live in a primary database
file, and the legacy reference objects (vehicles, customers, users) are
available under the `DATIDBSTORICO` schema backed by a separate file. Both
file locations SHALL be overridable by configuration. Dev mode SHALL enforce
SQLite foreign keys so owned-table constraints behave as they do in
production.

#### Scenario: Reference data resolves without MSSQL

- **WHEN** the app runs in dev mode and a request reads vehicles, customers, or users
- **THEN** the rows are served from the local SQLite files under the `DATIDBSTORICO` schema, with the same response shape as the MSSQL configuration

#### Scenario: Foreign keys are enforced

- **WHEN** a delete is attempted on an owned record still referenced by another owned record (for example a refrigerator referenced by a repair)
- **THEN** the request is rejected with the standard HTTP 409 conflict, as with the MSSQL database

#### Scenario: Custom database locations

- **WHEN** the dev database location is overridden by configuration
- **THEN** dev mode uses the overridden file path and the default location is not created

### Requirement: Explicit idempotent dev initialization

A `flask dev-init` command SHALL prepare the dev databases: apply the
owned-table schema at the current migration revision, create the external
`DATIDBSTORICO` tables if missing, and seed them with the prebaked seed data
when they are empty. Re-running the command on an initialized database SHALL
be a no-op (no duplicated seed rows, existing rows untouched). The
application SHALL NOT create or modify database objects at startup; database
initialization happens only through this command.

#### Scenario: First initialization creates and seeds

- **WHEN** `flask dev-init` runs with no dev databases present
- **THEN** the owned tables exist at the current migration revision, the external tables exist, and the external tables contain the prebaked seed rows

#### Scenario: Re-running initialization is a no-op

- **WHEN** `flask dev-init` runs a second time on an initialized dev database that contains rows created through the API
- **THEN** it succeeds, leaves the API-created rows untouched, and adds no duplicate seed rows

### Requirement: Prebaked external reference data

The prebaked dev seed data SHALL be committed to the repository as an
editable SQL file and SHALL contain, derived from the `clienti.sql` sample,
at least one customer, one vehicle, and one user. After initialization the
read-only reference endpoints SHALL return the seeded rows, and repairs
created through the API SHALL be able to reference the seeded customer and
vehicle.

#### Scenario: Seeded reference data is listed

- **WHEN** dev mode is initialized and a client GETs /api/v1/customers, /api/v1/vehicles, or /api/v1/users
- **THEN** each response includes the corresponding seeded row with the same field structure as the MSSQL configuration

#### Scenario: Seeded references are usable in repairs

- **WHEN** a repair is created via POST /api/v1/repairs using the seeded customer id and vehicle id
- **THEN** the repair is created (HTTP 201) with those references

#### Scenario: Unseeded references are still rejected

- **WHEN** a repair is created via POST /api/v1/repairs using a customer id that is not present in the seeded data
- **THEN** the request is rejected with HTTP 409

### Requirement: Customizable seed data

The seed data used by initialization SHALL be replaceable: configuration
SHALL allow pointing initialization at a custom SQL file instead of the
committed prebaked one, and custom files SHALL use the same statement shape
(INSERTs into the external tables). A modified or custom seed SHALL take
effect through the reset flow, not through a plain re-initialization.

#### Scenario: Custom seed file is used

- **WHEN** initialization with reset runs while configuration points at a custom seed file
- **THEN** the external tables contain the custom file's rows instead of the prebaked ones

#### Scenario: Editing the prebaked seed

- **WHEN** the developer edits the committed seed file and re-initializes with reset
- **THEN** the external tables reflect the edited rows

### Requirement: Full dev reset

A reset option of the `flask dev-init` command SHALL discard all dev data:
the owned tables SHALL be dropped and recreated empty at the current
migration revision, and the external tables SHALL be dropped, recreated, and
re-seeded with the active seed data. Reset SHALL NOT delete uploaded picture
files from the filesystem.

#### Scenario: Reset wipes dev data and reseeds

- **WHEN** the dev databases contain API-created repairs and equipment and reset is run
- **THEN** all owned tables are empty at the current migration revision and the external tables contain exactly the seed rows again

#### Scenario: Reset is safe on a fresh environment

- **WHEN** reset is run before any initialization
- **THEN** it succeeds and leaves the dev databases in the initialized, seeded state

### Requirement: API transparency in dev mode

In dev mode every `/api/v1` endpoint, health endpoint, and error behavior
SHALL be identical to the MSSQL configuration: same paths, response shapes,
status codes, and `{"error": "message"}` error envelope. Dev mode changes
only the backing database; no endpoint SHALL behave differently because of
it.

#### Scenario: Health reports readiness

- **WHEN** the app is running in initialized dev mode
- **THEN** GET /healthz responds 200 and GET /healthz/db reports the database reachable

#### Scenario: Error semantics unchanged

- **WHEN** a client writes to a read-only reference endpoint (for example POST /api/v1/customers) in dev mode
- **THEN** the response is HTTP 405, as with the MSSQL configuration
