# Tasks

## 1. Backend start-date upper bound

- [x] 1.1 In `app/services/repairs.py`, make a date-only `start_date_to` compare with `Repairs.start_data < start_to + timedelta(days=1)` (a full datetime keeps `<=`); verify the new `tests/test_api_repairs.py` case that lists a mid-day repair via a date-only `start_date_to` passes with `pytest tests/test_api_repairs.py`.

## 2. Repair page vehicle plate

- [x] 2.1 In `frontend/src/api/reference.ts`, add `getVehicle(id)` calling `GET /api/v1/vehicles/{vehicle_id}`; verify it type-checks in the build.
- [x] 2.2 In `frontend/src/pages/RepairPage.tsx`, seed the Targa field with `#id` and then resolve the plate via `getVehicle`, keeping the fallback on failure and not overwriting a newer selection; verify a new `RepairPage.test.tsx` case shows the plate for a loaded repair and `npm test` passes.

## 3. Repairs list and landing columns

- [x] 3.1 In `frontend/src/pages/RepairsListPage.tsx`, add a **Delivery date** column (`delivery_date`) and render **End date** from `end_data`; verify `RepairsListPage.test.tsx` asserts both cells and `npm test` passes.
- [x] 3.2 In `frontend/src/pages/HomePage.tsx`, label the delivery-date column **Delivery date**; verify `HomePage.test.tsx` still passes with `npm test`.

## 4. Integration verification

- [x] 4.1 Run `pytest` and, in `frontend/`, `npm test` and `npm run build`; verify the repairs tests and all frontend tests pass with no new regressions (the six pre-existing `tests/test_api_settings.py` failures, confirmed on `master`, and the pre-existing ruff findings are unchanged).
