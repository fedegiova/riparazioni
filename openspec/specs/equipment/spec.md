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
notes, archived flag). Full weight SHALL be required at
creation; a request without it SHALL be rejected. Remaining weight SHALL
default to the full weight when omitted at creation and MAY be set once at
creation. After creation the remaining weight SHALL be read-only on the update
path: an update carrying it SHALL be rejected, so the balance changes only
through refills and gas movements. Deleting a cylinder that
a work-log entry references SHALL be rejected.

#### Scenario: Remaining weight defaults to full weight
- **WHEN** a cylinder is created with full weight 10.0 and no remaining weight
- **THEN** the created record's remaining weight is 10.0

#### Scenario: Update a cylinder
- **WHEN** a client updates a cylinder's gas kind
- **THEN** the system responds with HTTP 200 and the change is persisted

#### Scenario: Manual balance change is rejected
- **WHEN** a client updates a cylinder with a remaining weight
- **THEN** the system responds with HTTP 400 and the balance is unchanged

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

### Requirement: Read a gas cylinder's operation log
The system SHALL return, for a gas cylinder, the log of every gas-affecting
operation on it: each refill recorded for the cylinder and each gas recharge or
recovery recorded on a work-log entry that references it. The log SHALL contain
only operations that concern the requested cylinder.

#### Scenario: Refills are included
- **WHEN** a client GETs /api/v1/gas-cylinders/<id>/operations for a cylinder that has refills
- **THEN** the response contains one entry per refill with its date and reference

#### Scenario: Gas movements are included
- **WHEN** a client GETs /api/v1/gas-cylinders/<id>/operations for a cylinder referenced by work-log entries carrying a recharge and a recovery
- **THEN** the response contains one entry per movement with the recharged and recovered weights recorded on it

#### Scenario: Only the requested cylinder's operations are returned
- **WHEN** the log is requested for a cylinder while other cylinders have movements
- **THEN** the response contains none of the other cylinders' operations

#### Scenario: Unknown cylinder
- **WHEN** a client GETs /api/v1/gas-cylinders/<id>/operations for a non-existent ID
- **THEN** the system responds with HTTP 404

#### Scenario: Cylinder with no operations
- **WHEN** a client requests the log for a cylinder with no refills or movements
- **THEN** the system responds with HTTP 200 and an empty log

### Requirement: Operation log entries carry their source references
Each operation-log entry SHALL identify its kind (refill, recharge, recovery, or a
combined recovery-and-recharge) and its date, and SHALL reference its source
record: a refill entry SHALL carry the refill's reference text, and a
gas-movement entry SHALL carry the repair id, the work-log entry id, and the
operator that recorded it.

#### Scenario: Refill entry carries the reference
- **WHEN** a refill recorded with reference "Supplier X" appears in the log
- **THEN** its entry reports kind refill, its date, and the reference "Supplier X"

#### Scenario: Recharge entry references its work log
- **WHEN** a recharge is recorded by operator "Mario" on a work-log entry of a repair
- **THEN** its log entry reports kind recharge, the repair id, the work-log entry id, the operator "Mario", and the recharged weight

#### Scenario: Recovery entry references its work log
- **WHEN** a recovery is recorded on a work-log entry of a repair
- **THEN** its log entry reports kind recovery, the repair id, the work-log entry id, and the recovered weight

### Requirement: Operation log is ordered newest first
The system SHALL merge refills and gas movements into a single sequence ordered
by the operation's time, most recent first.

#### Scenario: Mixed operations are ordered newest first
- **WHEN** a cylinder has a refill on one date and gas movements on later work-log dates
- **THEN** each response entry appears before those with an earlier time

### Requirement: Operation log reports a running remaining weight
Each operation-log entry SHALL report the cylinder's remaining weight after that
operation, reconstructed from the cylinder's creation by replaying the log in
chronological order: a recharge subtracts its recharged weight, a recovery adds
its recovered weight, a combined operation applies both, and a refill resets the
balance to the full weight.

#### Scenario: Recharge lowers the running balance
- **WHEN** a cylinder created full at 10.0 has a recharge of 2.5
- **THEN** the recharge entry reports a remaining weight of 7.5

#### Scenario: Recovery raises the running balance
- **WHEN** a recovery of 1.0 follows a balance of 7.5
- **THEN** the recovery entry reports a remaining weight of 8.5

#### Scenario: Combined operation applies both weights
- **WHEN** a recovery of 1.0 and a recharge of 2.5 are recorded together against a balance of 10.0
- **THEN** the entry reports a remaining weight of 8.5

#### Scenario: Refill resets the running balance to full
- **WHEN** a refill is recorded for a cylinder whose balance is 2.0 and full weight is 10.0
- **THEN** the refill entry reports a remaining weight of 10.0

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
