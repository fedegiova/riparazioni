# reference-data Specification

## Purpose

Read-only access to the pre-existing legacy objects — vehicles, customers,
and users — that repair records reference; no write operations are
exposed.

## Requirements

### Requirement: Read vehicles
The system SHALL return a list of vehicles and a single vehicle by ID
from the pre-existing vehicles table, including identifier, license plate
(targa), vehicle, body, model, and class fields.

#### Scenario: List vehicles
- **WHEN** a client GETs /api/v1/vehicles
- **THEN** the system responds with HTTP 200 with vehicle records including identifier and license plate

#### Scenario: Vehicle detail
- **WHEN** a client GETs /api/v1/vehicles/<id> for an existing vehicle
- **THEN** the system responds with HTTP 200 and the vehicle record

#### Scenario: Unknown vehicle
- **WHEN** a client GETs /api/v1/vehicles/<id> with a non-existent ID
- **THEN** the system responds with HTTP 404

#### Scenario: Writes are not exposed
- **WHEN** a client sends a POST, PUT, or DELETE to any /api/v1/vehicles endpoint
- **THEN** the system responds with HTTP 405

### Requirement: Read customers
The system SHALL return a list of customers and a single customer by ID
from the pre-existing customers view, including name, address, phone,
mobile, and email fields.

#### Scenario: List customers
- **WHEN** a client GETs /api/v1/customers
- **THEN** the system responds with HTTP 200 with customer records including identifier and name

#### Scenario: Unknown customer
- **WHEN** a client GETs /api/v1/customers/<id> with a non-existent ID
- **THEN** the system responds with HTTP 404

### Requirement: Read users
The system SHALL return a list of users and a single user by ID from the
pre-existing users table. Responses SHALL NOT include the password field.

#### Scenario: User detail excludes the password
- **WHEN** a client GETs /api/v1/users/<id> for an existing user
- **THEN** the system responds with HTTP 200 with the user's name and last login and no password field

#### Scenario: Unknown user
- **WHEN** a client GETs /api/v1/users/<id> with a non-existent ID
- **THEN** the system responds with HTTP 404

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
