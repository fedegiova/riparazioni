# settings Specification

## Purpose

Application-wide settings stored as name/value pairs, exposed over the API as
JSON and editable from the UI, with validated shapes for the known settings
(operators, working hours, holidays).

## Requirements

### Requirement: Read settings

The system SHALL expose stored application settings over the API: the full set
as a name-to-value map, and a single setting by name. Each value SHALL be
exchanged as a JSON document. A known setting that has never been written SHALL
read as its default value; an unknown setting name SHALL respond with 404.

#### Scenario: List returns stored settings

- **WHEN** a client GETs /api/v1/settings
- **THEN** the system responds with HTTP 200 and an object whose keys are setting names and whose values are the stored JSON values

#### Scenario: Read a single stored setting

- **WHEN** a client GETs /api/v1/settings/<name> for a stored setting
- **THEN** the system responds with HTTP 200 and that setting's JSON value

#### Scenario: Read an unwritten known setting returns its default

- **WHEN** a client GETs /api/v1/settings/operators and no operators have been stored
- **THEN** the system responds with HTTP 200 and an empty JSON array

#### Scenario: Read an unknown setting

- **WHEN** a client GETs /api/v1/settings/<name> for a name that is neither stored nor a known setting
- **THEN** the system responds with HTTP 404

### Requirement: Write settings

The system SHALL allow creating or replacing a single setting by name (upsert)
and updating several settings in one request. A multi-setting update SHALL be
atomic: if any value is rejected, no setting is changed. An unknown setting
name SHALL accept any JSON value.

#### Scenario: Upsert a setting

- **WHEN** a client PUTs /api/v1/settings/<name> with a JSON value
- **THEN** the system responds with HTTP 200, and a subsequent read returns the same value

#### Scenario: Bulk update applies every value

- **WHEN** a client PUTs /api/v1/settings with an object of multiple known settings
- **THEN** the system responds with HTTP 200 and a subsequent list read returns all of the updated values

#### Scenario: Bulk update with an invalid value changes nothing

- **WHEN** a client PUTs /api/v1/settings where one value is invalid for its known setting
- **THEN** the system responds with HTTP 400 and none of the settings are changed

#### Scenario: Unknown setting accepts any JSON

- **WHEN** a client PUTs /api/v1/settings/<name> for an unknown name with any JSON value
- **THEN** the system responds with HTTP 200 and stores that value

### Requirement: Validate known settings

On write, the system SHALL validate the value of each known setting and reject
an invalid value with HTTP 400 and the error envelope, leaving stored data
unchanged.

#### Scenario: Reject invalid operators

- **WHEN** a client writes the operators setting with a value that is not an array of strings
- **THEN** the system responds with HTTP 400 and the stored operators are unchanged

#### Scenario: Reject invalid working hours

- **WHEN** a client writes the working_hours setting with a malformed interval
- **THEN** the system responds with HTTP 400 and the stored working hours are unchanged

#### Scenario: Reject invalid holidays

- **WHEN** a client writes the holidays setting with a range outside its year
- **THEN** the system responds with HTTP 400 and the stored holidays are unchanged

### Requirement: Delete a setting

The system SHALL allow deleting a setting by name. Deleting a known setting
SHALL revert it to its default value on subsequent reads.

#### Scenario: Delete a known setting reverts to default

- **WHEN** a client DELETEs /api/v1/settings/operators after operators were stored
- **THEN** the system responds with HTTP 204 and a subsequent read returns the default empty array

#### Scenario: Delete an unknown setting

- **WHEN** a client DELETEs /api/v1/settings/<name> for a name that has no stored value
- **THEN** the system responds with HTTP 404

### Requirement: Operators setting

The `operators` setting SHALL be a JSON array of operator names, each a
non-empty string.

#### Scenario: Operators round-trip

- **WHEN** a client writes the operators setting with `["MARIO", "LUIGI"]`
- **THEN** the system responds with HTTP 200 and a subsequent read returns the same array

### Requirement: Working hours setting

The `working_hours` setting SHALL be a JSON object mapping weekday names
(`mon`..`sun`) to that day's list of working intervals. Each interval SHALL be a
two-element array of `HH:MM` times with the begin strictly before the end; a day
with an empty list is closed.

#### Scenario: Working hours round-trip

- **WHEN** a client writes working_hours with a Monday of `[["08:00","12:00"],["14:00","18:00"]]` and an empty Sunday
- **THEN** the system responds with HTTP 200 and a subsequent read returns the same object

#### Scenario: Reject an interval whose begin is not before its end

- **WHEN** a client writes a working_hours interval of `["18:00","08:00"]`
- **THEN** the system responds with HTTP 400

### Requirement: Holidays setting

The `holidays` setting SHALL be a JSON object mapping a four-digit year string
to that year's list of holiday ranges. Each range SHALL be an object with
`from` and `to` ISO dates and a non-empty `name`; both dates SHALL fall within
the mapped year and `from` SHALL not be after `to`. A closure spanning a year
boundary SHALL be represented as two ranges, one in each year.

#### Scenario: Holidays round-trip

- **WHEN** a client writes holidays with a 2026 range from `2026-08-10` to `2026-08-21` named "Ferie estive"
- **THEN** the system responds with HTTP 200 and a subsequent read returns the same object

#### Scenario: Reject a range outside its year

- **WHEN** a client writes a holiday range under year 2026 whose `to` date is in 2027
- **THEN** the system responds with HTTP 400
