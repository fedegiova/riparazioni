# Spec Delta

## MODIFIED Requirements

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
The system SHALL return a list of repairs, filterable by customer, vehicle, refrigerator, and a start-date range, and a single repair by ID. Each repair SHALL report the customer's resolved name and its total worked hours, computed as the sum of its work-log entry durations. The single-repair response SHALL additionally include its work-log entries and associated parts.

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

### Requirement: Gas recharge operations
When a work-log entry carries gas data, the system SHALL require a gas system state (VUOTO, PIENO, or RICUPERO_RICARICA). When a work-log entry records a gas recharge, the system SHALL require a cylinder reference and a recharged weight, and SHALL decrease that cylinder's remaining weight by the recharged amount in the same transaction; for RICUPERO_RICARICA the recovered weight SHALL be stored and SHALL NOT alter any cylinder balance. A recharged weight exceeding the cylinder's remaining weight SHALL be rejected.

#### Scenario: Recharge decreases cylinder balance
- **WHEN** a work-log entry is created with state VUOTO, recharged weight 2.5, and a cylinder whose remaining weight is 10.0
- **THEN** the entry stores the cylinder reference and weight, and the cylinder's remaining weight becomes 7.5

#### Scenario: Full system stores no gas data
- **WHEN** a work-log entry is created with state PIENO
- **THEN** the entry is stored without cylinder reference or weights

#### Scenario: Recovered weight is stored
- **WHEN** a work-log entry is created with state RICUPERO_RICARICA, recovered weight 1.0 and recharged weight 2.5
- **THEN** the entry stores both weights and the cylinder balance decreases only by the recharged amount

#### Scenario: Gas data without a state is rejected
- **WHEN** a work-log entry is created with a gas recharge but no gas system state
- **THEN** the system responds with HTTP 400 and no entry is created

#### Scenario: Overdraw is rejected
- **WHEN** a recharge of 12.0 is recorded against a cylinder whose remaining weight is 10.0
- **THEN** the system responds with HTTP 400, no entry is created, and the cylinder balance is unchanged

#### Scenario: Recharge without cylinder is rejected
- **WHEN** a gas recharge is recorded without a cylinder reference
- **THEN** the system responds with HTTP 400

## REMOVED Requirements

### Requirement: Repair type
**Reason**: The RIPA/RIPA_FRIGO distinction no longer matches how the workshop classifies work, and the UI never surfaces it. Gas handling no longer depends on it (see the modified Gas recharge operations requirement).
**Migration**: Drop the `type` column from REPAIRS. Clients must stop sending `type` on create/update and stop reading it; existing values are discarded.

## ADDED Requirements

### Requirement: Export repairs as an Excel workbook
The system SHALL provide a server-side export of repairs as a Microsoft Excel (`.xlsx`) file, honoring the same filters as the repairs list.

#### Scenario: Export all repairs
- **WHEN** a client GETs the repairs export endpoint
- **THEN** the system responds with HTTP 200 and an .xlsx file containing one row per repair

#### Scenario: Export honors filters
- **WHEN** a client requests the export with a customer filter
- **THEN** the file contains only that customer's repairs
