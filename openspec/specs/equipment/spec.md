# equipment Specification

## Purpose

CRUD management of the application's owned master data — refrigerators,
gas cylinders, and service parts — which repair records reference.

## Requirements

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
The system SHALL allow creating, listing, retrieving, updating, and deleting
gas cylinders (gas kind, serial number, model, full weight, remaining weight,
picture reference, notes, archived flag). Full weight SHALL be required at
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

### Requirement: Archive and restore gas cylinders
The system SHALL allow archiving a gas cylinder whose remaining weight is
below one quarter of its full weight, and restoring an archived cylinder.
Archiving and restoring SHALL leave the remaining weight unchanged. Listing
SHALL hide archived cylinders by default and include them when the archived
filter is requested.

#### Scenario: Archive a cylinder below one quarter
- **WHEN** a client archives a cylinder whose remaining weight is below one quarter of its full weight
- **THEN** the system responds with HTTP 200 and the cylinder is archived

#### Scenario: Archive above one quarter is rejected
- **WHEN** a client archives a cylinder whose remaining weight is at or above one quarter of its full weight
- **THEN** the system responds with HTTP 400 and the cylinder is not archived

#### Scenario: Restore keeps the balance
- **WHEN** a client restores an archived cylinder
- **THEN** the cylinder is active again and its remaining weight is unchanged

#### Scenario: Archived cylinders are hidden by default
- **WHEN** a client GETs /api/v1/gas-cylinders
- **THEN** the response omits archived cylinders; a request with the archived filter includes them

### Requirement: Record gas cylinder refills
The system SHALL record a refill for a gas cylinder, storing its date and
reference. Recording a refill SHALL set the cylinder's remaining weight to its
full weight and clear its archived flag in the same transaction. A refill
SHALL be allowed on any cylinder.

#### Scenario: Refill restores the full weight
- **WHEN** a client records a refill for a cylinder whose remaining weight is 2.0 and full weight is 10.0
- **THEN** the cylinder's remaining weight becomes 10.0

#### Scenario: Refill unarchives the cylinder
- **WHEN** a client records a refill for an archived cylinder
- **THEN** the cylinder is no longer archived

#### Scenario: Refills are listed per cylinder
- **WHEN** a client GETs a cylinder's refills
- **THEN** the response contains each recorded refill with its date and reference

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
