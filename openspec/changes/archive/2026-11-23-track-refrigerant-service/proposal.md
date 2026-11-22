# Proposal

## Why

Gas work logs currently identify a cylinder but do not require the serviced refrigerator, its nameplate charge, or a matching refrigerant. For F-gas traceability, the workshop needs to identify the unit and distinguish measured refrigerant input from calculated recovery without requiring two measurements for a combined operation.

## What Changes

- Extend existing refrigerator records with an allestimento link and a configured gas type, reusing the existing serial number, brand/manufacturer, model, and gas capacity fields. Manage installations and replacements from Anagrafica without writing to `TBALLESTIMENTI`.
- Allow at most one installed refrigerator per allestimento. Lock the serviced refrigerator to the repair on its first successful gas work log; ordinary repairs need no refrigerator.
- **BREAKING** for gas work-log writers: replace the legacy state-based input with None, Fill, Recovery, and Recovery + recharge. Require a matching cylinder and a linked refrigerator for gas operations. Fill is capped at nameplate capacity; recovery remains measured; combined work takes one measured net addition and calculates recovery from the nameplate.
- Use the new operation model for all gas work-log reads, writes, and cylinder history. Do not migrate old gas entries or retain legacy state handling. Keep cylinder balances, measured and calculated weights, and the gross `gas_used` export consistent under the new model.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `equipment`: Manage refrigerator installations, nameplate capacity, and gas type; distinguish measured and calculated weights in cylinder history.
- `anagrafica-ui`: Create, edit, and replace refrigerators from Allestimenti while keeping legacy data read-only.
- `repairs`: Lock repair equipment and validate, persist, and reverse operation-based gas movements.
- `repairs-ui`: Select the operation, enter only the applicable quantities, and explain equipment or cylinder blockers.
- `warehouse-ui`: Identify the measured net addition and calculated recovery in the cylinder log.

## Impact

Owned database schema and Alembic migrations (SQL Server and SQLite); refrigerator, repair, work-log, and cylinder-operation APIs; OpenAPI and generated frontend types; Anagrafica, repair, work-log, and cylinder-log screens; API and frontend tests. Existing `gas_types` settings are reused. External regulatory reporting and changes to legacy reference tables are out of scope.
