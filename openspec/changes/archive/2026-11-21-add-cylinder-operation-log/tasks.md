# Tasks

## 1. Backend operation-log endpoint

- [x] 1.1 In `app/routes/api/equipment.py`, add a helper that merges a cylinder's `refills` with the `RepairWorkLog` rows whose `gas_recharge` equals the cylinder id, maps each to an entry (`kind` refill, or recharge/recovery/recovery_recharge derived from `gas_system_state`, plus dates, weights, `repair_id`, `work_log_id`, `operator`, `reference`), and sorts newest-first with a deterministic tie-break; add `GET /api/v1/gas-cylinders/<id>/operations` using `_get_or_404`; verify `pytest tests/test_api_equipment.py` covers merged refills and movements, newest-first ordering, source references, an empty log returning `[]`, and an unknown id returning 404.
- [x] 1.2 Document the new endpoint and its entry shape in the README API section, and verify the documented path and fields match the implemented route (cross-check against `docs/openapi.yaml`).

## 2. OpenAPI contract and generated client

- [x] 2.1 Add `/api/v1/gas-cylinders/{cylinder_id}/operations` and its response schema to `docs/openapi.yaml`, reusing the existing cylinder path parameter; verify `pytest tests/test_openapi_contract.py` passes.
- [x] 2.2 Regenerate the frontend client (`npm run generate:api` in `frontend/`) and confirm the new operation types; verify `npm run build` type-checks.

## 3. Frontend operations API wrapper

- [x] 3.1 Add `getCylinderOperations(id)` to `frontend/src/api/equipment.ts` (calling the generated client) and re-export the operation entry type in `frontend/src/api/types.ts`; verify `frontend/src/api/equipment.test.ts` covers the request path and the returned array.

## 4. Cylinder operation-log page

- [x] 4.1 Create `frontend/src/pages/CylinderPage.tsx` showing the cylinder's identity and current state (full/remaining weight, archived) and its operation log (Date, Operation, Details, Reference) loaded with the `useApi` hook, newest first; register route `/magazzino/bombole/:id` in `frontend/src/App.tsx`; verify `frontend/src/pages/CylinderPage.test.tsx` covers the state, the log rows, a movement reference linking to `/repairs/:id`, a refill reference text, and the error state.
- [x] 4.2 Add a per-row log control in `frontend/src/components/CylindersManager.tsx` that navigates to the cylinder's page; verify `frontend/src/components/CylindersManager.test.tsx` covers the control navigating to the correct route.

## 5. Integration verification

- [x] 5.1 Run the full backend and frontend suites and lint (`pytest`, `npm test`, `npm run lint`, `npm run build` in `frontend/`); verify all exit 0 and that the existing cylinder refill/archive/balance behaviors are unchanged.

## 6. Running remaining weight

- [x] 6.1 In `app/routes/api/equipment.py`, compute the running remaining weight in `_cylinder_operations` by replaying the log oldest-first from `full_weight` (recharge subtracts, recovery adds, combined applies both, refill resets to full) and add `remaining_weight` to every entry; verify `pytest tests/test_api_equipment.py` covers the recharge, recovery, combined, and refill resulting balances.
- [x] 6.2 Add `remaining_weight` to the `CylinderOperation` schema in `docs/openapi.yaml`, regenerate the frontend client (`npm run generate:api`), and verify `pytest tests/test_openapi_contract.py` and `npm run build` pass.
- [x] 6.3 Add a Remaining column to `frontend/src/pages/CylinderPage.tsx`; verify `frontend/src/pages/CylinderPage.test.tsx` asserts an operation row's resulting weight.

## 7. Balance read-only after creation

- [x] 7.1 In `app/routes/api/equipment.py`, reject `remaining_weight` on the cylinder update path with 400 while keeping it accepted at creation; verify `pytest tests/test_api_equipment.py` covers the rejected manual change (balance unchanged) and that creation still seeds the balance.
- [x] 7.2 In `frontend/src/components/CylindersManager.tsx`, keep the remaining-weight (initial balance) field editable when creating a cylinder and render it read-only (disabled) when editing; ensure `toInput` sends `remaining_weight` only on create. Verify `frontend/src/components/CylindersManager.test.tsx` covers an editable balance on create (payload includes it), a read-only balance on edit, and that update payloads omit `remaining_weight`.
- [x] 7.3 Update the `PUT /api/v1/gas-cylinders/{id}` description in `docs/openapi.yaml` and the README so they no longer state that `remaining_weight` may be adjusted manually; verify the documented behavior matches the route.
- [x] 7.4 In `frontend/src/components/CylindersManager.tsx`, reject saving a new cylinder whose remaining weight exceeds its full weight (client-side only, no API change) and surface the error; verify `frontend/src/components/CylindersManager.test.tsx` covers the rejected over-full create and that a balance equal to full is accepted.

## 8. Integration verification

- [x] 8.1 Run the full backend and frontend suites and lint (`pytest`, `npm test`, `npm run lint`, `npm run build` in `frontend/`); verify all exit 0 and that the cylinder operation log, running balance, and read-only balance all behave as specified.
