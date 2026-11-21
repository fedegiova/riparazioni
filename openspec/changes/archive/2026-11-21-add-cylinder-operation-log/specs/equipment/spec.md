# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
