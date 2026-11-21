# Spec Delta

## ADDED Requirements

### Requirement: Gas types setting
The `gas_types` setting SHALL be a JSON array of gas type names, each a
non-empty string. When never written it SHALL read as an empty array.

#### Scenario: Gas types round-trip
- **WHEN** a client writes the gas_types setting with `["R410A", "R134a"]`
- **THEN** the system responds with HTTP 200 and a subsequent read returns the same array

#### Scenario: Unwritten gas_types reads as empty
- **WHEN** a client GETs /api/v1/settings/gas_types and no gas types have been stored
- **THEN** the system responds with HTTP 200 and an empty JSON array

#### Scenario: Reject invalid gas types
- **WHEN** a client writes the gas_types setting with a value that is not an array of strings
- **THEN** the system responds with HTTP 400 and the stored gas types are unchanged
