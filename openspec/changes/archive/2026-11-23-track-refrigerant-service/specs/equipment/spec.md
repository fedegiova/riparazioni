# Equipment delta

## ADDED Requirements

### Requirement: Refrigerator installations
The system SHALL allow registering a refrigerator against an existing allestimento and replacing the installed unit in one operation. At most one refrigerator SHALL be installed per allestimento. Linking SHALL require a serial number, manufacturer, model, positive finite nameplate capacity in kg, and gas type from the configured list. Legacy allestimento records SHALL remain read-only.

#### Scenario: Register against a known allestimento
- **WHEN** a client registers a refrigerator with complete nameplate data against an existing allestimento with no unit installed
- **THEN** the API returns the refrigerator and its allestimento link, and the refrigerator is discoverable by allestimento

#### Scenario: Reject an invalid installation
- **WHEN** a client links a refrigerator to an unknown allestimento, supplies incomplete or invalid nameplate data, or tries to add a second installed unit without explicitly replacing the current one
- **THEN** the API rejects the request and leaves existing installations unchanged

#### Scenario: Replace a refrigerator
- **WHEN** a client explicitly replaces the installed refrigerator with a different valid record
- **THEN** only the replacement is installed, and the old refrigerator record and references to it are preserved

#### Scenario: Delete an installed unit
- **WHEN** a client tries to delete an installed refrigerator
- **THEN** the system responds with HTTP 409 and the installation remains unchanged

### Requirement: Identify calculated cylinder-log weights
For a combined operation, the cylinder operation log SHALL expose the measured net addition, the total recharged weight, and the calculated recovered weight, identifying recovery as calculated. The running balance SHALL account for the net addition only once.

#### Scenario: Combined operation is visible in cylinder history
- **WHEN** the reconstructed balance before a new combined operation is 10.0 kg and the operation adds 0.4 kg net to a 3.0 kg refrigerator
- **THEN** the log reports 0.4 kg net added, 3.0 kg recharged, 2.6 kg recovered marked calculated, and a running balance of 9.6 kg for that movement
