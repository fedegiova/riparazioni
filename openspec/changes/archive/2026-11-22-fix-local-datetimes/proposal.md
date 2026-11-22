# Proposal

## Why

Repair start times and work-log start/end times are entered through a
`datetime-local` field, converted from local time to UTC before they are sent to
the API, and then rendered back verbatim on read. The write path converts, the
read path does not, so every timestamp is displayed shifted by the browser's UTC
offset (one to two hours in the workshop's CET/CEST timezone, sometimes moving
the date). The workshop is a single-site operation whose database stores naive
datetimes, so the stored value is meant to be local wall-clock time.

## What Changes

- Make the repairs/work-log write path emit local wall-clock time instead of
  UTC, matching the naive datetimes the backend stores and the read path already
  assumes: `toIso` no longer calls `toISOString()`.
- Make the "now" writes that bypass the field (archive a repair, stop a work-log
  entry) emit local wall-clock time too, via a shared helper, instead of
  `new Date().toISOString()`.
- Make the backend's default repair start datetime use local time, so a repair
  saved with an empty start field is not stored as a shifted UTC value.
- Add a round-trip regression test for a non-UTC local time plus targeted tests
  for the affected pages.
- No change to the stored format (still a naive ISO 8601 datetime) and no
  retroactive rewrite of existing rows.

## Capabilities

### New Capabilities
<!-- None: the behavior is a correction within existing capabilities. -->

### Modified Capabilities
- `repairs`: the start datetime is local wall-clock time and its default is the
  server's local current time, stored and returned without timezone conversion.
- `repairs-ui`: the repair and work-log screens send the entered wall-clock time
  unchanged and show the same wall-clock time back.

## Impact

- Frontend: `frontend/src/lib/format.ts` (`toIso`, new `nowIso`),
  `frontend/src/pages/RepairPage.tsx` (archive/stop now use `nowIso`).
- Backend: `app/models/owned.py` (default for `REPAIRS.start_data`).
- Tests: a new `frontend/src/lib/format.test.ts`; existing frontend page tests
  and `tests/test_api_repairs.py` default-time assertion.
- API contract: unchanged shape (`format: date-time`), so `docs/openapi.yaml`
  and the generated client need no structural change.
- Out of scope: picture `uploaded_date` and its storage-folder date, which are
  unrelated to repair/work-log timestamps; migrating existing rows already
  stored as UTC.
