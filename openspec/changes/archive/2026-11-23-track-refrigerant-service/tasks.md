# Tasks

## 1. Storage and installation API

- [x] 1.1 Check the deployed work-log schema, then add the installation fields, repair lock, and operation/cylinder/measurement fields with the filtered unique index. Verify SQLite upgrade, SQL Server migration DDL, uniqueness of installed units, and that the migration does not require obsolete gas columns or rewrite existing work logs or balances.
- [x] 1.2 Extend refrigerator CRUD in `app/routes/api/equipment.py` with installation validation, lookup/filtering, and guarded atomic replacement. Document the endpoints in `docs/openapi.yaml` and verify new and existing replacement records, invalid legacy IDs, incomplete nameplates, duplicate installs, and blocked deletion of installed or referenced units in `tests/test_api_equipment.py`.

## 2. Repair and gas accounting API

- [x] 2.1 Expose locked refrigerator identity and current installation status in repair detail. Resolve and lock the installed unit on first successful gas work and guard repair reassignment. Verify missing installation, replacement before and after first gas work, stale editor selection, and attempts to change the locked vehicle or refrigerator.
- [x] 2.2 Replace the old gas-state logic in `app/services/repairs.py` with the four operations and a single measured weight. Verify missing and mismatched gas types, combined math and its boundary values, fill capacity, overfill, overdraw, invalid input, and validation failure without timer, lock, or stock changes.
- [x] 2.3 Use the new movement model for edits, explicit None, deletions, cylinder history, and reports; coordinate cylinder/refill writes with the guard. Verify reversal, unchanged calculations after nameplate edits, and gross `gas_used` in the API and workbook. Remove the old gas-state contract from the API documentation and `docs/openapi.yaml`, then regenerate frontend types.

## 3. Workshop UI

- [x] 3.1 Add refrigerator installation, edit, and replacement to `frontend/src/pages/AnagraficaPage.tsx` using the configured gas types. Verify that successful saves refresh the vehicle row, failed requests are shown, and legacy vehicle/customer data remains read-only in `AnagraficaPage.test.tsx`.
- [x] 3.2 Replace the gas-state UI in `WorkLogPage.tsx` with the operation selector and show the locked unit in `RepairPage.tsx`. Verify the operation-specific labels, single measured input, calculated preview, matching cylinder filtering, blocker messages, explicit None reversal, and metadata-only edits.
- [x] 3.3 Use the new operation model in the warehouse cylinder history. Verify combined rows label measured net addition and calculated recovery and keep the link to the source repair.

## 4. Integration checks

- [x] 4.1 Exercise installation, first gas log, replacement, and cylinder reversal end to end. Verify with independent transactions that replacement cannot misbind a gas job and a concurrent refill or gas write cannot lose a stock update. Run the repair, equipment, settings, and migration regression tests, the frontend test suite, and the production frontend build.
