# settings Specification delta

## MODIFIED Requirements

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
- **THEN** the system responds with HTTP 200 and the configured default operator list

#### Scenario: Read an unknown setting

- **WHEN** a client GETs /api/v1/settings/<name> for a name that is neither stored nor a known setting
- **THEN** the system responds with HTTP 404

### Requirement: Delete a setting

The system SHALL allow deleting a setting by name. Deleting a known setting
SHALL revert it to its default value on subsequent reads.

#### Scenario: Delete a known setting reverts to default

- **WHEN** a client DELETEs /api/v1/settings/operators after operators were stored
- **THEN** the system responds with HTTP 204 and a subsequent read returns the configured default operator list

#### Scenario: Delete an unknown setting

- **WHEN** a client DELETEs /api/v1/settings/<name> for a name that has no stored value
- **THEN** the system responds with HTTP 404

### Requirement: Operators setting

The `operators` setting SHALL be a JSON array of operator names, each a
non-empty string. When never written it SHALL read as the configured default
operator list.

#### Scenario: Operators round-trip

- **WHEN** a client writes the operators setting with `["MARIO", "LUIGI"]`
- **THEN** the system responds with HTTP 200 and a subsequent read returns the same array

### Requirement: Working hours setting

The `working_hours` setting SHALL be a JSON object mapping weekday names
(`mon`..`sun`) to that day's list of working intervals. Each interval SHALL be a
two-element array of `HH:MM` times with the begin strictly before the end; a day
with an empty list is closed. When never written it SHALL read as the configured
default weekly schedule.

#### Scenario: Working hours round-trip

- **WHEN** a client writes working_hours with a Monday of `[["08:00","12:00"],["14:00","18:00"]]` and an empty Sunday
- **THEN** the system responds with HTTP 200 and a subsequent read returns the same object

#### Scenario: Reject an interval whose begin is not before its end

- **WHEN** a client writes a working_hours interval of `["18:00","08:00"]`
- **THEN** the system responds with HTTP 400

#### Scenario: Unwritten working hours reads as the default schedule

- **WHEN** a client GETs /api/v1/settings/working_hours and no schedule has been stored
- **THEN** the system responds with HTTP 200 and the configured default weekly schedule

### Requirement: Gas types setting

The `gas_types` setting SHALL be a JSON array of gas type names, each a
non-empty string. When never written it SHALL read as the configured default
gas type list.

#### Scenario: Gas types round-trip

- **WHEN** a client writes the gas_types setting with `["R410A", "R134a"]`
- **THEN** the system responds with HTTP 200 and a subsequent read returns the same array

#### Scenario: Unwritten gas types reads as empty

- **WHEN** a client GETs /api/v1/settings/gas_types and no gas types have been stored
- **THEN** the system responds with HTTP 200 and the configured default gas type list

#### Scenario: Reject invalid gas types

- **WHEN** a client writes the gas_types setting with a value that is not an array of strings
- **THEN** the system responds with HTTP 400 and the stored gas types are unchanged
