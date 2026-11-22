# Spec Delta

## MODIFIED Requirements

### Requirement: Retrieve repairs
The system SHALL return a list of repairs, filterable by customer, vehicle, refrigerator, and a start-date range, and a single repair by ID. A start-date upper bound supplied as a date (with no time) SHALL include the whole of that day. Each repair SHALL report the customer's resolved name and its total worked hours, computed as the sum of its work-log entry durations. The single-repair response SHALL additionally include its work-log entries, associated parts, and pictures.

#### Scenario: List all repairs
- **WHEN** a client GETs /api/v1/repairs
- **THEN** the system responds with HTTP 200 and, for each repair, the customer name and total worked hours alongside the repair fields

#### Scenario: Total hours sums work-log durations
- **WHEN** a repair has work-log entries of 1h30 and 2h00
- **THEN** the repair's total hours is 3h30

#### Scenario: Filter by customer
- **WHEN** a client GETs /api/v1/repairs?customer=<id>
- **THEN** the response contains only repairs for that customer

#### Scenario: Start-date upper bound includes the whole day
- **WHEN** a client GETs /api/v1/repairs?start_date_to=2026-11-01 and a repair starts at 2026-11-01T10:00:00
- **THEN** the response contains that repair

#### Scenario: Repair detail includes work log and parts
- **WHEN** a client GETs /api/v1/repairs/<id> for a repair with two work-log entries and one part
- **THEN** the response includes the repair with its two work-log entries and one part entry

#### Scenario: Unknown repair
- **WHEN** a client GETs /api/v1/repairs/<id> with a non-existent ID
- **THEN** the system responds with HTTP 404

#### Scenario: Repair detail includes pictures
- **WHEN** a client GETs /api/v1/repairs/<id> for a repair that has pictures
- **THEN** the response includes the repair with its pictures
