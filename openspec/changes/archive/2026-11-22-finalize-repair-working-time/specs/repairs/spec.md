# Spec Delta

## MODIFIED Requirements

### Requirement: Retrieve repairs
The system SHALL return a list of repairs, filterable by customer, vehicle, refrigerator, and a start-date range, and a single repair by ID. A date-only upper bound SHALL include the whole day. Each repair SHALL report the resolved customer name and `total_hours` as numeric hours: the live adjusted total for an active repair and the frozen total for an archived repair. The single-repair response SHALL also include work logs, parts, and pictures.

#### Scenario: List all repairs
- **WHEN** a client GETs /api/v1/repairs
- **THEN** the system responds with HTTP 200 and, for each repair, the customer name and total worked hours alongside the repair fields

#### Scenario: Total hours sums work-log durations
- **WHEN** an active repair has completed work-log entries of 1h30 and 2h00 fully within working intervals and outside vacation dates
- **THEN** the repair's total hours is 3h30 in both list and detail responses

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

### Requirement: Update a repair
The system SHALL allow updating a repair's customer, vehicle, refrigerator, notes, delivery date, and end datetime. Setting the end datetime on an active repair SHALL archive it and save the adjusted total in the same transaction, unless a running timer blocks archiving. Clearing the end datetime SHALL reopen the repair and restore live calculation. Updating an already-archived repair without reopening it SHALL NOT recalculate the frozen total.

#### Scenario: Complete a repair
- **WHEN** a client updates an active repair with an end datetime and no timers are running on it
- **THEN** the system responds with HTTP 200, saves the end datetime and adjusted total, and returns the saved total in `total_hours`

#### Scenario: Running timers prevent archiving
- **WHEN** a client sets an end datetime on an active repair with a work log that has a start time and no end time
- **THEN** the system responds with HTTP 409, identifies the blocking timers and their operators where known, and leaves the repair and its logs unchanged

#### Scenario: Reopen a completed repair
- **WHEN** a client updates a completed repair with a null end datetime
- **THEN** the end datetime is cleared and `total_hours` is once again calculated from the current calendar and work logs

#### Scenario: Re-archive a reopened repair
- **WHEN** a client archives a reopened repair after its running timers have been stopped
- **THEN** the system freezes a new total using the calendar and logs in effect at that archive

#### Scenario: Change the requested delivery date
- **WHEN** a client updates a repair's delivery date
- **THEN** the system responds with HTTP 200 and the new delivery date is stored

### Requirement: Work log entries
The system SHALL allow adding, updating, and deleting work-log entries on an active repair. Entries SHALL support start time, end time, operator, and an optional text description. Creating an entry SHALL require an operator from the configured list. The system SHALL reject adding, editing, or deleting individual work logs on archived repairs until they are reopened.

#### Scenario: Add a work log entry
- **WHEN** a client POSTs to /api/v1/repairs/<id>/work-log with a start time and a configured operator
- **THEN** the system responds with HTTP 201 and the entry appears in the repair detail

#### Scenario: Description round-trips
- **WHEN** a client creates or updates a work log with a text description
- **THEN** the saved description is returned in the work-log response and subsequent repair detail; existing logs without a description remain readable

#### Scenario: Invalid operator on creation
- **WHEN** a client creates a work log without an operator or with an unconfigured operator
- **THEN** the system responds with HTTP 400 without creating a log or stopping any timer

#### Scenario: Delete a work log entry
- **WHEN** a client DELETEs a work-log entry from an active repair and the entry recorded no gas recharge
- **THEN** the system responds with HTTP 204 and the entry is removed from the repair

#### Scenario: Archived work logs are read-only
- **WHEN** a client tries to add, edit, or delete a work-log entry on an archived repair
- **THEN** the system responds with HTTP 409 and leaves logs, cylinder balances, and the frozen total unchanged

#### Scenario: Work log on unknown repair
- **WHEN** a client POSTs a work-log entry to a non-existent repair ID
- **THEN** the system responds with HTTP 404

### Requirement: Export repairs as an Excel workbook
The system SHALL provide a server-side export of repairs as a Microsoft Excel (`.xlsx`) file, honoring the same filters as the repairs list and using the same `total_hours` values.

#### Scenario: Export all repairs
- **WHEN** a client GETs the repairs export endpoint
- **THEN** the system responds with HTTP 200 and an .xlsx file containing one row per repair

#### Scenario: Export honors filters
- **WHEN** a client requests the export with a customer filter
- **THEN** the file contains only that customer's repairs

#### Scenario: Export matches API totals
- **WHEN** a client exports a list with active and archived repairs
- **THEN** the workbook reports the same live and frozen values as the repair list for the same logs and settings

## ADDED Requirements

### Requirement: Calendar-adjusted working time
The system SHALL compute live `total_hours` by summing each completed work log's overlap with the configured weekday working intervals in local wall-clock time, excluding every date within a configured vacation range, inclusive. Overlapping configured intervals SHALL count once per log, and separate logs SHALL be summed independently. A log without a positive completed interval SHALL contribute zero.

#### Scenario: Lunch and time outside the schedule do not count
- **WHEN** a log runs from 11:30 to 17:00 on a day with working intervals 08:00–12:00 and 13:00–16:30
- **THEN** the log contributes 4 hours

#### Scenario: A multi-day log skips vacation dates and closed days
- **WHEN** a log spans several dates, including a closed weekday and both endpoint dates of a vacation range
- **THEN** only working intervals on dates outside the closure and vacation contribute

#### Scenario: Calendar corrections change the live total
- **WHEN** a manager adds a vacation covering an active repair's completed log
- **THEN** a subsequent read excludes the work logged on that date

#### Scenario: Overlapping schedules are not double counted
- **WHEN** two operators each log 10:00–11:00 and overlapping configured intervals cover that hour
- **THEN** each log contributes one hour and the total is two hours

#### Scenario: Running or incomplete logs contribute zero
- **WHEN** a repair has only running or incomplete work logs
- **THEN** its live `total_hours` is zero

### Requirement: Preserve archived working time
While a repair is archived, the system SHALL report its frozen `total_hours` regardless of future calendar changes. Repairs archived before the feature is introduced SHALL retain the elapsed work-log totals shown before rollout until explicitly reopened.

#### Scenario: Calendar changes do not affect archived repairs
- **WHEN** working hours or vacations change after a repair is archived
- **THEN** its reported total does not change

#### Scenario: Previously archived repair retains its total
- **WHEN** an already-archived repair with logged time outside the current schedule is read after rollout
- **THEN** it retains the total it reported before rollout, including that time

### Requirement: Hand off an operator's running work log
When a client creates a running work log (a start time and no end time), the system SHALL stop any running logs for the same operator on active repairs at the new log's start time, in the same transaction as creation. It SHALL NOT stop other operators' logs or perform a handoff when recording a completed historical entry.

#### Scenario: Operator starts work on another repair
- **WHEN** an operator with a running log starts a new timer on the same or a different active repair
- **THEN** the prior log's end time equals the new log's start time, the new log is running, and other operators' timers are unchanged

#### Scenario: Historical entry does not stop a timer
- **WHEN** an operator with a running timer creates an entry with both start and end times
- **THEN** the historical entry is recorded and the running timer is unchanged

#### Scenario: Backdating would end the previous timer before its start
- **WHEN** the new timer's start precedes a running log's start for that operator
- **THEN** the system rejects the creation and leaves all existing timers unchanged

#### Scenario: Failed creation does not stop the previous timer
- **WHEN** a new timer fails validation, including any gas movement validation
- **THEN** no timer is created or stopped and no cylinder balance changes

#### Scenario: Concurrent starts do not leave duplicate running timers
- **WHEN** two requests try to start a timer concurrently for the same operator
- **THEN** the resulting state contains at most one running timer for that operator on active repairs
