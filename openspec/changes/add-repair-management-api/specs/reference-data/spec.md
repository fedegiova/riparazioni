# Spec Delta

## Purpose

Read-only access to the pre-existing legacy objects — vehicles, customers,
and users — that repair records reference; no write operations are
exposed.

## ADDED Requirements

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
