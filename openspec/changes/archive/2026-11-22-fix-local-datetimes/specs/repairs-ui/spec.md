# Spec Delta

## ADDED Requirements

### Requirement: Repair and work-log times are entered and shown as local wall-clock time

The application SHALL send a repair start date and work-log start/end times as
the local wall-clock value entered in the field, without converting it to UTC,
and SHALL show the stored value back unchanged. The "now" actions that bypass
the field — archiving a repair and stopping a work-log entry — SHALL record the
local current wall-clock time.

#### Scenario: An entered repair start is shown unchanged after saving

- **WHEN** the user saves a repair whose Start date is `2026-11-22T00:07` and reopens it
- **THEN** the Start date field shows `2026-11-22T00:07`

#### Scenario: Entered work-log times are shown unchanged after saving

- **WHEN** the user saves a work-log entry with start `2026-11-22T00:13` and end `2026-11-22T01:43` and reopens it
- **THEN** the start and end fields show `2026-11-22T00:13` and `2026-11-22T01:43`

#### Scenario: Archiving records the local current time

- **WHEN** the user archives a repair
- **THEN** the end datetime sent to the API is the local current wall-clock time, not the UTC time

#### Scenario: Stopping a work-log entry records the local current time

- **WHEN** the user stops an open work-log entry
- **THEN** the end time sent to the API is the local current wall-clock time, not the UTC time
