# Spec Delta

## ADDED Requirements

### Requirement: Dev-mode external schema name
In dev mode the legacy reference objects SHALL be attached and addressed
under the configured schema name (default `DATIDBSTORICO`). Because SQLite
attaches a single file under one name, dev mode SHALL refuse to start with a
clear error when the configured qualifier is a cross-database 3-part name,
rather than silently mismatching the attached schema.

#### Scenario: Attach uses the configured name
- **WHEN** the app starts in dev mode with the default schema qualifier
- **THEN** the external SQLite file is attached as `DATIDBSTORICO` and the reference endpoints resolve against it

#### Scenario: Cross-database qualifier is rejected
- **WHEN** the app starts in dev mode with the schema qualifier set to a 3-part cross-database name (for example `AHR_GIOPLAST.DATIDBSTORICO`)
- **THEN** startup fails with an error naming the setting and stating that dev mode needs the bare SQLite schema name
