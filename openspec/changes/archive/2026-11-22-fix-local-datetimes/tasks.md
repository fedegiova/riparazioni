# Tasks

## 1. Frontend datetime helpers

- [x] 1.1 In `frontend/src/lib/format.ts`, make `toIso` emit a naive local ISO datetime (append `:00` seconds when missing, return `undefined` for empty/invalid input, no `toISOString()`) and add a `nowIso()` helper built on `nowDateTimeInput()`; verify a new `frontend/src/lib/format.test.ts` covers the non-UTC round trip `2026-11-22T00:07` → `2026-11-22T00:07:00`, the empty case, and `nowIso()` staying local.
- [x] 1.2 Verify `toDateTimeInput`/`formatDateTime` slice a stored `...:00` value back to the entered `YYYY-MM-DDTHH:MM` (add assertions to `format.test.ts`).

## 2. Frontend pages

- [x] 2.1 In `frontend/src/pages/RepairPage.tsx`, send the entered start via `toIso` and replace the archive (`end_data`) and stop (`end_time`) `new Date().toISOString()` calls with `nowIso()`; verify `RepairPage.test.tsx` asserts the save payload carries the local value and the archive/stop payloads are local (no `Z`/offset).
- [x] 2.2 Verify `WorkLogPage.test.tsx` asserts a saved entry's `start_time`/`end_time` equal the field values unchanged (local, no `Z`).

## 3. Backend default start datetime

- [x] 3.1 In `app/models/owned.py`, give `REPAIRS.start_data` a local-time default (leaving `uploaded_date`'s UTC default untouched) and update the `_now()` helper in `tests/test_api_repairs.py` so the default assertion is local; verify `pytest tests/test_api_repairs.py -k defaults_to_now` passes.

## 4. Integration verification

- [x] 4.1 Run the full suites and build (`pytest`, and `npm test`, `npm run lint`, `npm run build` in `frontend/`) and verify all exit 0 with no regressions in the existing repair/work-log tests.
