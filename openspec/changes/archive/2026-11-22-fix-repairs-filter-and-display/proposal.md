# Proposal

## Why

Three confirmed defects in the repairs screens reported after the last test pass
(`reports/03`–`05`) are not covered by the automated suites: the repairs list
date filter drops repairs started later on the selected end day, the repair page
shows a vehicle's numeric id instead of its plate, and the repairs list "End
date" column shows the requested delivery date rather than the actual end date.

## What Changes

- Make a date-only `start_date_to` filter bound include the whole selected day,
  so "Start to = today" no longer hides repairs created today. The same fix
  covers the export endpoint, which reuses the list filters.
- Resolve and show the vehicle's plate on the repair page when an existing
  repair is loaded, keeping the `#id` fallback only when the lookup fails.
- On the full repairs list, show both a **Delivery date** column (the requested
  delivery date) and an **End date** column (the actual close datetime, blank
  while the repair is open).
- On the active-repairs landing, label the column that shows the requested
  delivery date **Delivery date**, since the landing lists only repairs with no
  end date.
- Add regression tests for each defect.

## Capabilities

### New Capabilities
<!-- None: the changes correct behavior within existing capabilities. -->

### Modified Capabilities
- `repairs`: the start-date range filter's upper bound is inclusive of the whole
  day when given as a date.
- `repairs-ui`: the repair page shows the loaded vehicle's plate; the repairs
  list shows both delivery and end dates; the landing labels its delivery-date
  column correctly.

## Impact

- Backend: `app/services/repairs.py` (`list_repairs`), `tests/test_api_repairs.py`.
- Frontend: `frontend/src/api/reference.ts`, `frontend/src/pages/RepairPage.tsx`,
  `frontend/src/pages/RepairsListPage.tsx`, `frontend/src/pages/HomePage.tsx`,
  and their tests.
- API contract: unchanged; no `docs/openapi.yaml` or generated-client change.
