# Spec Delta

## ADDED Requirements

### Requirement: Configurable legacy schema qualifier
The system SHALL qualify the pre-existing reference objects (vehicles,
customers, users) with a single configurable schema name, defaulting to
`DATIDBSTORICO`. When configured with a cross-database 3-part name such as
`AHR_GIOPLAST.DATIDBSTORICO`, the system SHALL emit that qualifier on every
statement against those objects so SQL Server resolves them in the
`AHR_GIOPLAST` database.

#### Scenario: Default qualifier resolves on SQLite
- **WHEN** the schema qualifier is left at its default and a client GETs /api/v1/vehicles, /api/v1/customers, or /api/v1/users in dev mode or tests
- **THEN** the statements target the `DATIDBSTORICO` schema and the endpoints respond with HTTP 200

#### Scenario: Cross-database qualifier resolves on SQL Server
- **WHEN** the schema qualifier is set to `AHR_GIOPLAST.DATIDBSTORICO` and the app runs against SQL Server
- **THEN** the reference queries are issued against the `AHR_GIOPLAST.DATIDBSTORICO` schema and the reference endpoints respond with HTTP 200 instead of failing

#### Scenario: External objects stay out of migrations
- **WHEN** an Alembic autogenerate or upgrade runs with a configured qualifier
- **THEN** the pre-existing reference objects are excluded from the migration, whatever the qualifier, and no external object is created or dropped
