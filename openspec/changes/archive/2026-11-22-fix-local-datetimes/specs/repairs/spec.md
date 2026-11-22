# Spec Delta

## ADDED Requirements

### Requirement: Datetimes are local wall-clock time

Repair and work-log datetimes SHALL be interpreted as local wall-clock time. A
client-supplied start datetime or work-log start/end time SHALL be stored and
returned unchanged, with no timezone conversion; a defaulted repair start
datetime SHALL be the server's local current time.

#### Scenario: A client-supplied start datetime is stored verbatim

- **WHEN** a client creates a repair with `start_data` `2026-11-22T00:07:00`
- **THEN** the stored and returned `start_data` is `2026-11-22T00:07:00`, with no offset applied

#### Scenario: A work-log time is stored verbatim

- **WHEN** a client adds a work-log entry with `start_time` `2026-11-22T00:13:00` and `end_time` `2026-11-22T01:43:00`
- **THEN** the entry is stored and returned with exactly those times, unshifted

#### Scenario: An omitted start datetime defaults to local time

- **WHEN** a repair is created without a start datetime
- **THEN** the stored start datetime is the server's local current time, not its UTC time
