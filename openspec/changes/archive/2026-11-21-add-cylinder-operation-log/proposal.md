# Proposal

## Why

Gas cylinders accumulate history from three places — refills, gas recharges,
and gas recoveries recorded while working on a repair — but the warehouse
screen only shows a cylinder's current balance. Nobody can answer "where did
this cylinder's gas go?" or "which repairs used this cylinder?" without hunting
through repair work logs. A per-cylinder page that lists every operation, each
linked back to its source record, makes the cylinder's life auditable from one
place.

## What Changes

- Add a read endpoint `GET /api/v1/gas-cylinders/{cylinder_id}/operations` that
  returns the cylinder's operation log: its refills plus every gas recharge and
  recovery recorded on a work-log entry that references the cylinder, merged into
  one chronologically ordered list (newest first).
- Each log entry carries the operation's date/time, a kind (refill, recharge, or
  recovery), the gas weights involved, and **references** to its source: for a
  refill the stored reference text, and for a gas movement the repair id, the
  work-log entry id, and the operator.
- Add a cylinder detail page at `/magazzino/bombole/:id`, reached from the
  Bombole tab of the warehouse page, showing the cylinder's identity and current
  state above its operation-log table (Date, Operation, Details, Reference), with
  the reference linking to the source repair or work-log entry.
- No new tables: the log is derived from the existing `REFILLS` and
  `REPAIR_WORK_LOG` rows, so nothing is duplicated or backfilled.

## Capabilities

### New Capabilities
<!-- None: the behavior extends existing capabilities. -->

### Modified Capabilities
- `equipment`: adds a per-cylinder operation-log read endpoint aggregating
  refills and gas movements with source references.
- `warehouse-ui`: adds a per-cylinder operation-log page reached from the
  Bombole tab.

## Impact

- Backend: a new aggregating read (in `app/routes/api/equipment.py` or a small
  `app/services/equipment.py` helper) over `Refill` and `RepairWorkLog`; no model
  or migration changes.
- API contract: `docs/openapi.yaml` gains the endpoint and its response schema;
  the generated frontend client is regenerated.
- Frontend: a new `frontend/src/api/` wrapper, a new
  `frontend/src/pages/CylinderPage.tsx`, a route in `frontend/src/App.tsx`, and a
  navigation control in `frontend/src/components/CylindersManager.tsx`.
- Tests: backend route tests (aggregation, ordering, references, unknown
  cylinder) and the OpenAPI contract test; frontend page/api tests.
- Out of scope: recording edits, creation, archive and restore as operations,
  and any cylinder actions on the new page (it is read-only); the existing
  warehouse controls keep handling writes.
