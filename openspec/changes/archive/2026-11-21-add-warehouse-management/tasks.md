# Tasks

## 1. Schema and models

- [x] 1.1 Add `archived` (boolean, default false) to `GasCylinder`, make `full_weight` non-nullable, add a `Refill` model (`id`, `gas_cylinder_id` FK, `date`, `reference`) and add `RECUPERO` to `GAS_SYSTEM_STATES` in `app/models/owned.py`; verify `pytest tests/test_models.py` passes with new assertions for the fields and table.
- [x] 1.2 Create the Alembic revision (revises `75d9543863f9`) creating `REFILLS`, adding `GAS_CYLINDERS.archived` with a `0` server default, and tightening `full_weight` to NOT NULL with `op.batch_alter_table` (no backfill — the database is empty); verify `flask dev-init --reset` (or `alembic upgrade head`) reaches head and `pytest tests/test_migration.py` passes.

## 2. `gas_types` setting

- [x] 2.1 Register `gas_types` in `app/services/settings.py` (`_DEFAULT_FACTORIES` → `list`, `_VALIDATORS` → list of non-empty strings); verify new cases in `tests/test_api_settings.py` pass: round-trip, unwritten-reads-empty, and reject-not-a-list-of-strings.

## 3. Equipment API: required `full_weight`, archive, refill

- [x] 3.1 Reject create/update of a gas cylinder without `full_weight` (HTTP 400) in `app/routes/api/equipment.py`; verify `pytest tests/test_api_equipment.py` create-without-full-weight case passes.
- [x] 3.2 Add archive and restore endpoints enforcing `remaining_weight < full_weight / 4` at archive time and leaving the balance unchanged on both; verify tests covering archive-below, archive-at-or-above (400), and restore-keeps-balance.
- [x] 3.3 Add refill endpoints (create + list per cylinder) that set `remaining_weight := full_weight` and `archived := false` in one transaction; verify tests for restore-to-full, unarchive-on-refill, and refill listing with date/reference.
- [x] 3.4 Exclude archived cylinders from the default list and include them with an `?archived=true` filter; verify a test asserting the default response omits an archived cylinder and the filtered one includes it.
- [x] 3.5 Update the existing equipment tests that create cylinders without `full_weight`; verify `pytest tests/test_api_equipment.py` passes fully.

## 4. Gas accounting in repairs

- [x] 4.1 Rewrite `_validate_gas` in `app/services/repairs.py` to the state/field matrix plus overdraw (`< 0`) and overfill (`> full_weight`) rejection; verify tests in `tests/test_api_repairs.py` for VUOTO, PIENO, RECUPERO, RICUPERO_RICARICA, no-state, overdraw, and overfill.
- [x] 4.2 Apply `remaining += recovered - recharged` in `_apply_gas` and reverse both movements symmetrically on update and delete (replacing `_restore_recharge` call sites); verify tests for recovery-increases, the RICUPERO_RICARICA net result, and delete reversal.
- [x] 4.3 Attach a read-time `gas_used` field (sum of recharged weights) to repair serialization and add it to the Excel export columns; verify tests summing recharges, the zero case, and the export column.
- [x] 4.4 Update the gas-fields section of `README.md` to describe the corrected accounting (recovery adds, recharge subtracts, independent fields, RECUPERO); verify the documented behavior matches the implemented tests.

## 5. OpenAPI contract and generated client

- [x] 5.1 Update `docs/openapi.yaml` with the `archived` field, archive/restore/refill paths, the `RECUPERO` enum value, the `gas_used` repair field, and `full_weight` as required; verify `pytest tests/test_openapi_contract.py` passes.
- [x] 5.2 Regenerate the frontend client (`npm run generate:api`) and add the CRUD/archive/restore/refill wrappers in `frontend/src/api/equipment.ts` plus a `gas_types` accessor in `frontend/src/api/settings.ts`; verify `npm run build` type-checks against the new client.

## 6. Settings UI: gas type list editor

- [x] 6.1 Add a gas-type list editor to `frontend/src/pages/SettingsPage.tsx` that loads and saves with the other settings; verify `frontend/src/pages/SettingsPage.test.tsx` add/remove round-trip passes.

## 7. Warehouse UI: tab shell and spares

- [x] 7.1 Replace the `MagazzinoPage` placeholder with a tabbed shell (Ricambi, Ricambi Frigo, Bombole) with Ricambi selected by default; verify a page test renders the tabs and the default panel.
- [x] 7.2 Build the shared part management component (list, create, edit, delete) parameterized by `is_refrigerator_part` and wire it to both part tabs; verify a page test exercises create/edit/delete against a mocked API for both flags.
- [x] 7.3 Add frontend tests for the part API wrappers; verify `frontend/src/api` wrapper tests pass.

## 8. Warehouse UI: gas cylinders

- [x] 8.1 Build the cylinder list with the state overview (per-cylinder fill indicator and a summary of states); verify a page test renders the overview and rows including remaining/full weights.
- [x] 8.2 Build the cylinder editor with the gas-type picker sourced from `gas_types`; verify a page test asserts configured gas types appear as choices.
- [x] 8.3 Add the refill, archive, restore, and delete actions, surfacing backend errors (e.g. a referenced-cylinder 409); verify page tests for each action and the error message.
- [x] 8.4 Add frontend tests for the cylinder/refill API wrappers; verify `frontend/src/api` wrapper tests pass.

## 9. Integration verification

- [x] 9.1 Run the full backend and frontend suites and lint (`pytest`, `npm test`, `npm run lint`, `npm run build`); verify all exit 0, then apply the change artifacts are consistent with the observed behavior.
