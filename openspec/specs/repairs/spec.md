# repairs Specification

## Purpose

Manages the repair lifecycle: creating RIPA and RIPA FRIGO repair records,
recording work-log entries and used parts, and performing gas-recharge
operations that keep gas-cylinder balances current.

## Requirements

### Requirement: Create a repair
The system SHALL allow creating a repair with customer, vehicle, optional refrigerator, notes, start datetime, and an optional delivery date. The start datetime SHALL default to the current time when omitted. The created record SHALL receive a sequential identifier.

#### Scenario: Create a RIPA FRIGO repair
- **WHEN** a client POSTs to /api/v1/repairs with a valid customer ID, a valid vehicle ID, and a delivery date
- **THEN** the system responds with HTTP 201 and the created repair including its identifier, start datetime, and delivery date

#### Scenario: Start datetime defaults to now
- **WHEN** a repair is created without a start datetime
- **THEN** the stored start datetime equals the time of creation

#### Scenario: Unknown customer is rejected
- **WHEN** a repair is created with a customer ID that does not exist in the customers reference data
- **THEN** the system responds with HTTP 409 and no repair is created

### Requirement: Retrieve repairs
The system SHALL return a list of repairs, filterable by customer, vehicle, refrigerator, and a start-date range, and a single repair by ID. Each repair SHALL report the customer's resolved name and its total worked hours, computed as the sum of its work-log entry durations. The single-repair response SHALL additionally include its work-log entries, associated parts, and pictures.

#### Scenario: List all repairs
- **WHEN** a client GETs /api/v1/repairs
- **THEN** the system responds with HTTP 200 and, for each repair, the customer name and total worked hours alongside the repair fields

#### Scenario: Total hours sums work-log durations
- **WHEN** a repair has work-log entries of 1h30 and 2h00
- **THEN** the repair's total hours is 3h30

#### Scenario: Filter by customer
- **WHEN** a client GETs /api/v1/repairs?customer=<id>
- **THEN** the response contains only repairs for that customer

#### Scenario: Repair detail includes work log and parts
- **WHEN** a client GETs /api/v1/repairs/<id> for a repair with two work-log entries and one part
- **THEN** the response includes the repair with its two work-log entries and one part entry

#### Scenario: Unknown repair
- **WHEN** a client GETs /api/v1/repairs/<id> with a non-existent ID
- **THEN** the system responds with HTTP 404

#### Scenario: Repair detail includes pictures
- **WHEN** a client GETs /api/v1/repairs/<id> for a repair that has pictures
- **THEN** the response includes the repair with its pictures

### Requirement: Update a repair
The system SHALL allow updating a repair's customer, vehicle, refrigerator, notes, delivery date, and end datetime. Setting the end datetime marks the repair completed; clearing it reopens the repair.

#### Scenario: Complete a repair
- **WHEN** a client updates a repair with an end datetime
- **THEN** the system responds with HTTP 200 and the repair's end datetime is stored

#### Scenario: Reopen a completed repair
- **WHEN** a client updates a completed repair with a null end datetime
- **THEN** the repair's end datetime is cleared

#### Scenario: Change the requested delivery date
- **WHEN** a client updates a repair's delivery date
- **THEN** the system responds with HTTP 200 and the new delivery date is stored

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
When a work-log entry carries gas data, the system SHALL require a gas system
state (VUOTO, PIENO, RECUPERO, or RICUPERO_RICARICA). The system SHALL apply
each gas movement to the cylinder referenced by the entry in the same
transaction, storing recharged and recovered weights as independent values: a
recharged weight SHALL decrease the cylinder's remaining weight and a recovered
weight SHALL increase it. A recharge SHALL require a cylinder and a positive
recharged weight; a recovery SHALL require a cylinder and a non-negative
recovered weight; PIENO SHALL carry no cylinder or weights. A movement taking
the balance below zero or above the cylinder's full weight SHALL be rejected.

#### Scenario: Recharge decreases cylinder balance
- **WHEN** a work-log entry is created with state VUOTO, recharged weight 2.5, and a cylinder whose remaining weight is 10.0
- **THEN** the entry stores the cylinder reference and weight, and the cylinder's remaining weight becomes 7.5

#### Scenario: Full system stores no gas data
- **WHEN** a work-log entry is created with state PIENO
- **THEN** the entry is stored without cylinder reference or weights

#### Scenario: Recovered weight is stored
- **WHEN** a work-log entry is created with state RECUPERO and recovered weight 1.0 against a cylinder whose remaining weight is 4.0
- **THEN** the entry stores the recovered weight and the cylinder's remaining weight becomes 5.0

#### Scenario: Recover and recharge apply independently
- **WHEN** a work-log entry is created with state RICUPERO_RICARICA, recovered weight 1.0 and recharged weight 2.5 against a cylinder whose remaining weight is 10.0
- **THEN** the entry stores both weights and the cylinder's remaining weight becomes 8.5

#### Scenario: Gas data without a state is rejected
- **WHEN** a work-log entry is created with a gas recharge but no gas system state
- **THEN** the system responds with HTTP 400 and no entry is created

#### Scenario: Overdraw is rejected
- **WHEN** a recharge of 12.0 is recorded against a cylinder whose remaining weight is 10.0
- **THEN** the system responds with HTTP 400, no entry is created, and the cylinder balance is unchanged

#### Scenario: Overfill is rejected
- **WHEN** a recovery would take a cylinder's balance above its full weight
- **THEN** the system responds with HTTP 400 and the cylinder balance is unchanged

#### Scenario: Recharge without cylinder is rejected
- **WHEN** a gas recharge is recorded without a cylinder reference
- **THEN** the system responds with HTTP 400

### Requirement: Deleting a recharge entry restores the balance
Deleting a work-log entry that recorded gas movements SHALL reverse them in the
same transaction: the cylinder's remaining weight SHALL increase by the
recharged amount and decrease by the recovered amount.

#### Scenario: Balance is restored on delete
- **WHEN** a work-log entry that recharged 2.5 and recovered 1.0 from a cylinder is deleted
- **THEN** the cylinder's remaining weight has increased by 1.5

### Requirement: Report gas used per repair
The system SHALL report, for a repair, the total recharged gas weight as the sum
of the recharged weights recorded on its work-log entries.

#### Scenario: Gas total sums recharges
- **WHEN** a repair has work-log entries recharging 2.5 and 1.0
- **THEN** the repair's reported gas used is 3.5

#### Scenario: No recharges reports zero
- **WHEN** a repair has no work-log entry carrying a recharged weight
- **THEN** the repair's reported gas used is 0

### Requirement: Export repairs as an Excel workbook
The system SHALL provide a server-side export of repairs as a Microsoft Excel (`.xlsx`) file, honoring the same filters as the repairs list.

#### Scenario: Export all repairs
- **WHEN** a client GETs the repairs export endpoint
- **THEN** the system responds with HTTP 200 and an .xlsx file containing one row per repair

#### Scenario: Export honors filters
- **WHEN** a client requests the export with a customer filter
- **THEN** the file contains only that customer's repairs

### Requirement: Datetimes are local wall-clock time
Repair and work-log datetimes SHALL be interpreted as local wall-clock time. A client-supplied start datetime or work-log start/end time SHALL be stored and returned unchanged, with no timezone conversion; a defaulted repair start datetime SHALL be the server's local current time.

#### Scenario: A client-supplied start datetime is stored verbatim
- **WHEN** a client creates a repair with `start_data` `2026-11-22T00:07:00`
- **THEN** the stored and returned `start_data` is `2026-11-22T00:07:00`, with no offset applied

#### Scenario: A work-log time is stored verbatim
- **WHEN** a client adds a work-log entry with `start_time` `2026-11-22T00:13:00` and `end_time` `2026-11-22T01:43:00`
- **THEN** the entry is stored and returned with exactly those times, unshifted

#### Scenario: An omitted start datetime defaults to local time
- **WHEN** a repair is created without a start datetime
- **THEN** the stored start datetime is the server's local current time, not its UTC time
