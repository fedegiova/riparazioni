# Spec Delta

## Purpose

Manages the repair lifecycle: creating RIPA and RIPA FRIGO repair records,
recording work-log entries and used parts, and performing gas-recharge
operations that keep gas-cylinder balances current.

## ADDED Requirements

### Requirement: Create a repair
The system SHALL allow creating a repair with customer, vehicle, type
(RIPA or RIPA_FRIGO), optional refrigerator, notes, and start datetime.
The start datetime SHALL default to the current time when omitted. The
created record SHALL receive a sequential identifier.

#### Scenario: Create a RIPA FRIGO repair
- **WHEN** a client POSTs to /api/v1/repairs with a valid customer ID, valid vehicle ID, type RIPA_FRIGO and a refrigerator ID
- **THEN** the system responds with HTTP 201 and the created repair including its identifier and start datetime

#### Scenario: Start datetime defaults to now
- **WHEN** a repair is created without a start datetime
- **THEN** the stored start datetime equals the time of creation

#### Scenario: Unknown customer is rejected
- **WHEN** a repair is created with a customer ID that does not exist in the customers reference data
- **THEN** the system responds with HTTP 409 and no repair is created

### Requirement: Repair type
The system SHALL store each repair's type as RIPA or RIPA_FRIGO and SHALL
reject any other value on create or update.

#### Scenario: Invalid type is rejected
- **WHEN** a repair is created or updated with a type other than RIPA or RIPA_FRIGO
- **THEN** the system responds with HTTP 400 with a validation error

### Requirement: Retrieve repairs
The system SHALL return a list of repairs, filterable by customer,
vehicle, refrigerator, type, and start-date range, and a single repair by
ID. The single-repair response SHALL include its work-log entries and its
associated parts.

#### Scenario: List all repairs
- **WHEN** a client GETs /api/v1/repairs
- **THEN** the system responds with HTTP 200 and a list of repair records

#### Scenario: Filter by customer
- **WHEN** a client GETs /api/v1/repairs?customer=<id>
- **THEN** the response contains only repairs for that customer

#### Scenario: Repair detail includes work log and parts
- **WHEN** a client GETs /api/v1/repairs/<id> for a repair with two work-log entries and one part
- **THEN** the response includes the repair with its two work-log entries and one part entry

#### Scenario: Unknown repair
- **WHEN** a client GETs /api/v1/repairs/<id> with a non-existent ID
- **THEN** the system responds with HTTP 404

### Requirement: Update a repair
The system SHALL allow updating a repair's customer, vehicle,
refrigerator, type, notes, and end datetime. Setting the end datetime
marks the repair completed; clearing it reopens the repair.

#### Scenario: Complete a repair
- **WHEN** a client updates a repair with an end datetime
- **THEN** the system responds with HTTP 200 and the repair's end datetime is stored

#### Scenario: Reopen a completed repair
- **WHEN** a client updates a completed repair with a null end datetime
- **THEN** the repair's end datetime is cleared

### Requirement: Delete a repair
The system SHALL allow deleting a repair; its work-log entries and part
associations SHALL be removed with it.

#### Scenario: Deleting a repair cascades
- **WHEN** a client DELETEs a repair that has work-log entries and parts
- **THEN** the system responds with HTTP 204 and the repair's work-log entries and part rows no longer exist

### Requirement: Associate parts with a repair
The system SHALL allow associating service parts with a repair, each with
a quantity and an optional unit price, when creating or updating the
repair, and SHALL include the parts in the repair detail.

#### Scenario: Create a repair with parts
- **WHEN** a repair is created with a parts array containing a valid part ID and quantity 2
- **THEN** the part association is stored and the repair detail lists the part with quantity 2

#### Scenario: Unknown part is rejected
- **WHEN** a repair references a part ID that does not exist
- **THEN** the system responds with HTTP 409 and no repair or association is created

### Requirement: Work log entries
The system SHALL allow adding, updating, and deleting work-log entries on
a repair, each with start time, end time, and operator.

#### Scenario: Add a work log entry
- **WHEN** a client POSTs to /api/v1/repairs/<id>/work-log with a start time and operator
- **THEN** the system responds with HTTP 201 and the entry appears in the repair detail

#### Scenario: Delete a work log entry
- **WHEN** a client DELETEs a work-log entry that recorded no gas recharge
- **THEN** the system responds with HTTP 204 and the entry is removed from the repair

#### Scenario: Work log on unknown repair
- **WHEN** a client POSTs a work-log entry to a non-existent repair ID
- **THEN** the system responds with HTTP 404

### Requirement: Gas recharge operations
When a work-log entry records a gas recharge, the system SHALL require a
cylinder reference and a recharged weight, and SHALL decrease that
cylinder's remaining weight by the recharged amount in the same
transaction. For RIPA_FRIGO repairs the entry SHALL also record the gas
system state (VUOTO, PIENO, or RICUPERO_RICARICA); for RICUPERO_RICARICA
the recovered weight SHALL be stored and SHALL NOT alter any cylinder
balance. A recharged weight exceeding the cylinder's remaining weight
SHALL be rejected.

#### Scenario: Recharge decreases cylinder balance
- **WHEN** a work-log entry is created with state VUOTO, recharged weight 2.5, and a cylinder whose remaining weight is 10.0
- **THEN** the entry stores the cylinder reference and weight, and the cylinder's remaining weight becomes 7.5

#### Scenario: Full system stores no gas data
- **WHEN** a work-log entry is created with state PIENO
- **THEN** the entry is stored without cylinder reference or weights

#### Scenario: Recovered weight is stored
- **WHEN** a work-log entry is created with state RICUPERO_RICARICA, recovered weight 1.0 and recharged weight 2.5
- **THEN** the entry stores both weights and the cylinder balance decreases only by the recharged amount

#### Scenario: Overdraw is rejected
- **WHEN** a recharge of 12.0 is recorded against a cylinder whose remaining weight is 10.0
- **THEN** the system responds with HTTP 400, no entry is created, and the cylinder balance is unchanged

#### Scenario: Recharge without cylinder is rejected
- **WHEN** a gas recharge is recorded without a cylinder reference
- **THEN** the system responds with HTTP 400

### Requirement: Deleting a recharge entry restores the balance
Deleting a work-log entry that recorded a gas recharge SHALL restore the
cylinder's remaining weight by the recharged amount.

#### Scenario: Balance is restored on delete
- **WHEN** a work-log entry that recharged 2.5 from a cylinder is deleted
- **THEN** the cylinder's remaining weight has increased by 2.5
