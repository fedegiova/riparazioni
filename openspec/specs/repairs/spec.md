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
The system SHALL allow updating a repair's customer, vehicle, refrigerator, notes, delivery date, and end datetime, subject to the gas-work refrigerator lock. Setting the end datetime on an active repair SHALL archive it and save the adjusted total in the same transaction, unless a running timer blocks archiving. Clearing the end datetime SHALL reopen the repair and restore live calculation. Updating an already-archived repair without reopening it SHALL NOT recalculate the frozen total.

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
- **THEN** the change is stored and the system responds with HTTP 200

#### Scenario: Locked equipment cannot be reassigned
- **WHEN** a client tries to change or clear the vehicle or refrigerator on a repair locked by gas work
- **THEN** the system responds with HTTP 409 and leaves the repair unchanged

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

### Requirement: Record gas operations on work logs
Gas work SHALL use `none`, `fill`, `recovery`, or `recovery_recharge`. A missing operation SHALL record or display ordinary work when no gas data is supplied. Gas movement SHALL require one cylinder with a gas type matching the refrigerator and one finite measured amount in kg. The work log, repair lock, and cylinder movement SHALL be saved atomically; a resulting balance outside zero through cylinder capacity SHALL be rejected.

#### Scenario: None is ordinary work
- **WHEN** a client creates a work log with no gas data or explicitly selects `none` without any cylinder or weights
- **THEN** it is saved without a gas movement and without requiring an allestimento or refrigerator

#### Scenario: Recharge decreases cylinder balance
- **WHEN** a client records `fill` using a matching cylinder with enough stock and a positive amount at or below nameplate capacity
- **THEN** the entered weight is saved, reported as recharged weight, and subtracted from the cylinder

#### Scenario: Recovered weight is stored
- **WHEN** a client records `recovery` with a matching cylinder and a non-negative measured recovered weight that fits in the cylinder
- **THEN** the measured weight is stored and added to the cylinder balance

#### Scenario: Combined work uses one net measurement
- **WHEN** a client records `recovery_recharge` with a 3.0 kg nameplate and a measured net addition of 0.4 kg from a matching cylinder with 10.0 kg remaining
- **THEN** the system saves the 3.0 kg capacity used and the 0.4 kg measured net addition, reports 3.0 kg recharged and 2.6 kg calculated recovered, and leaves 9.6 kg in the cylinder

#### Scenario: Combined amount can be zero or equal to capacity
- **WHEN** a client explicitly records zero or the full nameplate capacity as net added, and the cylinder balance permits the movement
- **THEN** zero is accepted as no fresh gas used, and the full nameplate amount is accepted as zero calculated recovery

#### Scenario: Reject invalid gas inputs
- **WHEN** a gas write has an unknown or missing operation, incompatible fields, a missing cylinder or required measurement, a missing or mismatched gas type, a fill above nameplate capacity, a combined net addition outside zero through capacity, or a movement outside cylinder balance bounds
- **THEN** the write fails without changing the work log, repair lock, cylinder balance, or any running timer

#### Scenario: Gas data without an operation is rejected
- **WHEN** a client supplies gas movement data without `gas_operation`
- **THEN** the system responds with HTTP 400 and does not save a movement

#### Scenario: Overdraw is rejected
- **WHEN** a fill or combined operation needs more gas than the cylinder has available
- **THEN** the system responds with HTTP 400 without changing the cylinder or saving the movement

#### Scenario: Overfill is rejected
- **WHEN** a recovery would take the cylinder balance above its full weight
- **THEN** the system responds with HTTP 400 without changing the cylinder or saving the movement

#### Scenario: Recharge without cylinder is rejected
- **WHEN** a fill or combined operation has no cylinder reference
- **THEN** the system responds with HTTP 400 without saving the movement

#### Scenario: Edit or clear gas on an active work log
- **WHEN** a client successfully replaces the gas dataset or explicitly changes the operation to `none`
- **THEN** the system reverses the old stored movement and applies the replacement, if any, in the same transaction; omitting gas fields on update leaves them unchanged

#### Scenario: Existing ordinary work needs no conversion
- **WHEN** a work log without a recorded operation is read or edited without adding gas work
- **THEN** it is treated as ordinary work without requiring a refrigerator or generating a cylinder movement

### Requirement: Bind gas work to the installed refrigerator
New or changed gas work SHALL require an existing repair allestimento with a valid installed refrigerator. The first successful gas operation SHALL lock that unit to the repair. Later gas work on the repair SHALL use the locked unit only while it is still installed on that allestimento. Replacing the unit SHALL NOT alter the repair's recorded refrigerator or existing gas movements.

#### Scenario: First gas operation binds the installed unit
- **WHEN** a repair that is not yet locked records its first valid gas operation
- **THEN** the system resolves and locks the refrigerator installed at save time and returns its identity with the repair

#### Scenario: No installed unit blocks only gas work
- **WHEN** a client attempts a gas operation for a repair with no allestimento or no installed unit
- **THEN** the system rejects the gas write with an explanation, and an ordinary work log remains allowed

#### Scenario: Replacement after gas work requires a separate repair
- **WHEN** a different refrigerator is installed after the repair was locked and a client attempts to record further gas work on that repair
- **THEN** the system rejects the gas work and points to a separate repair for the replacement unit; the prior logs and lock are unchanged

#### Scenario: Historical calculation does not follow nameplate edits
- **WHEN** the nameplate capacity is edited after a combined operation was saved
- **THEN** reading, editing unrelated work-log fields, or reversing that operation uses the original recorded values, not the new capacity
