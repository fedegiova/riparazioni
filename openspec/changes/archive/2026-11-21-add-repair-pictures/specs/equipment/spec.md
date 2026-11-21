# Spec Delta

## MODIFIED Requirements

### Requirement: Manage gas cylinders
The system SHALL allow creating, listing, retrieving, updating, and deleting
gas cylinders (gas kind, serial number, model, full weight, remaining weight,
notes, archived flag). Full weight SHALL be required at
creation; a request without it SHALL be rejected. Remaining weight SHALL
default to the full weight when omitted at creation. Deleting a cylinder that
a work-log entry references SHALL be rejected.

#### Scenario: Remaining weight defaults to full weight
- **WHEN** a cylinder is created with full weight 10.0 and no remaining weight
- **THEN** the created record's remaining weight is 10.0

#### Scenario: Update a cylinder
- **WHEN** a client updates a cylinder's gas kind
- **THEN** the system responds with HTTP 200 and the change is persisted

#### Scenario: Delete a referenced cylinder
- **WHEN** a client DELETEs a cylinder referenced by a work-log entry
- **THEN** the system responds with HTTP 409 and the cylinder is not deleted

#### Scenario: Delete an unreferenced cylinder
- **WHEN** a client DELETEs a cylinder that no work-log entry references
- **THEN** the system responds with HTTP 204 and the record is gone

#### Scenario: Create without full weight is rejected
- **WHEN** a client POSTs to /api/v1/gas-cylinders without full weight
- **THEN** the system responds with HTTP 400 and no cylinder is created

### Requirement: Manage service parts
The system SHALL allow creating, listing, retrieving, updating, and
deleting service parts (name, supplier, kind, price,
is-refrigerator-part flag, notes). The list SHALL be
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
