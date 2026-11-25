# Spec Delta

## MODIFIED Requirements

### Requirement: Archive and restore gas cylinders
The system SHALL allow archiving a gas cylinder whose remaining weight is
below one quarter of its full weight, and restoring an archived cylinder.
Archiving and restoring SHALL leave the remaining weight unchanged. Listing
SHALL hide archived cylinders by default and include them when the archived
filter is requested. The archived filter SHALL return the same records on every
supported database (SQLite and SQL Server).

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

#### Scenario: Archived filter is database-portable
- **WHEN** a client GETs /api/v1/gas-cylinders on SQL Server
- **THEN** the request succeeds with HTTP 200 and the response omits archived cylinders, without a database syntax error

### Requirement: Manage service parts
The system SHALL allow creating, listing, retrieving, updating, and
deleting service parts (name, supplier, kind, price,
is-refrigerator-part flag, notes). The list SHALL be
filterable by the is-refrigerator-part flag. The filter SHALL return the same
records on every supported database (SQLite and SQL Server).

#### Scenario: Create a part
- **WHEN** a client POSTs to /api/v1/service-parts with name, price and kind
- **THEN** the system responds with HTTP 201 and the created record

#### Scenario: Filter parts by refrigerator flag
- **WHEN** a client GETs /api/v1/service-parts?is_refrigerator_part=true
- **THEN** the response contains only refrigerator parts

#### Scenario: Filter parts is database-portable
- **WHEN** a client GETs /api/v1/service-parts?is_refrigerator_part=true on SQL Server
- **THEN** the request succeeds with HTTP 200 and the response contains only refrigerator parts, without a database syntax error

#### Scenario: Delete a part used by a repair
- **WHEN** a client DELETEs a part associated with an existing repair
- **THEN** the system responds with HTTP 409 and the part is not deleted
