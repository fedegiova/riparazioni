# Proposal

## Why

Commit `Aggiungi operatori di default` made the `operators`, `working_hours`, and `gas_types` settings return non-empty defaults when never written, but the `settings` spec still says they read as empty. The tests were updated to match the code, so the spec is the last place that contradicts shipped behavior. Aligning it keeps the contract trustworthy for future changes.

## What Changes

- Update the `settings` spec so a known-but-unwritten `operators` setting reads as its configured default list rather than an empty array.
- Document that an unwritten `gas_types` setting reads as its configured default list rather than an empty array.
- Document the default `working_hours` schedule returned when the setting was never written.
- Clarify that deleting a known setting reverts it to that setting's default value (which may be non-empty), replacing the "default empty array" wording.
- No code or API behavior changes: this only makes the spec match current behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `settings`: correct the documented defaults for `operators`, `working_hours`, and `gas_types`, and the "delete reverts to default" wording.

## Impact

Specification only. No application code, API, database, or frontend changes. The existing settings tests already assert the real defaults.
