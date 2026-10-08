# Spec Delta

## Purpose

CRUD management of the application's owned master data — refrigerators,
gas cylinders, and service parts — which repair records reference.

## ADDED Requirements

### Requirement: Manage refrigerators
The system SHALL allow creating, listing, retrieving, updating, and
deleting refrigerators (serial number, model, brand, gas weight, notes).

#### Scenario: Create a refrigerator
- **WHEN** a client POSTs to /api/v1/refrigerators with serial number, model and brand
- **THEN** the system responds with HTTP 201 and the created record

#### Scenario: List refrigerators
- **WHEN** a client GETs /api/v1/refrigerators
- **THEN** the system responds with HTTP 200 and all refrigerator records

#### Scenario: Update a refrigerator
- **WHEN** a client updates a refrigerator's model
- **THEN** the system responds with HTTP 200 and the change is persisted

#### Scenario: Delete a referenced refrigerator
- **WHEN** a client DELETEs a refrigerator referenced by an existing repair
- **THEN** the system responds with HTTP 409 and the refrigerator is not deleted

#### Scenario: Delete an unreferenced refrigerator
- **WHEN** a client DELETEs a refrigerator that no repair references
- **THEN** the system responds with HTTP 204 and the record is gone

### Requirement: Manage gas cylinders
The system SHALL allow creating, listing, retrieving, updating, and
deleting gas cylinders (gas kind, serial number, model, full weight,
remaining weight, picture reference, notes). The remaining weight SHALL
default to the full weight when omitted at creation.

#### Scenario: Remaining weight defaults to full weight
- **WHEN** a cylinder is created with full weight 10.0 and no remaining weight
- **THEN** the created record's remaining weight is 10.0

#### Scenario: Update a cylinder
- **WHEN** a client updates a cylinder's gas kind
- **THEN** the system responds with HTTP 200 and the change is persisted

#### Scenario: Delete a referenced cylinder
- **WHEN** a client DELETEs a cylinder referenced by a work-log entry
- **THEN** the system responds with HTTP 409 and the cylinder is not deleted

### Requirement: Manage service parts
The system SHALL allow creating, listing, retrieving, updating, and
deleting service parts (name, supplier, kind, price,
is-refrigerator-part flag, picture reference, notes). The list SHALL be
filterable by the is-refrigerator-part flag.

#### Scenario: Create a part
- **WHEN** a client POSTs to /api/v1/service-parts with name, price and kind
- **THEN** the system responds with HTTP 201 and the created record

#### Scenario: Filter parts by refrigerator flag
- **WHEN** a client GETs /api/v1/service-parts?is_refrigerator_part=true
- **THEN** the response contains only refrigerator parts

#### Scenario: Delete a part used by a repair
- **WHEN** a client DELETEs a part associated with an existing repair
- **THEN** the system responds with HTTP 409 and the part is not deleted
