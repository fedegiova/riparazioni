# Proposal

## Why

The workshop UI (planned as a separate frontend change) needs repairs data the
API does not yet expose: a customer-requested delivery date, each repair's
total worked hours, and customer names instead of raw ids. At the same time the
repair `type` field (`RIPA` / `RIPA_FRIGO`) no longer reflects how the shop
works and blocks the UI, so it should be removed rather than worked around.
The shop also needs to export the repair list to Excel from the server.

## What Changes

- **BREAKING** Remove the `type` field from repairs (create, update, list,
  detail, OpenAPI, spec). The gas rule that previously keyed off `RIPA_FRIGO`
  becomes: **any** work-log entry carrying gas data requires a
  `gas_system_state`.
- Add a nullable **`delivery_date`** to repairs — the delivery date requested
  by the customer (distinct from `end_data`, the actual close timestamp).
- Add a computed **`total_hours`** to the repairs list and detail responses:
  the sum of the repair's work-log entry durations (`end_time - start_time`).
- Resolve and include the **customer name** in the repairs list and detail
  responses (from the read-only customers reference data), alongside the
  customer id.
- Add a server-side **Excel export** endpoint for repairs that streams a real
  `.xlsx` file (via `openpyxl`).
- Migration: drop `REPAIRS.type`, add `REPAIRS.delivery_date`.

## Capabilities

### New Capabilities
<!-- None: all changes land on the existing `repairs` capability. -->

### Modified Capabilities
- `repairs`: remove the repair `type` requirement; add the `delivery_date`
  field; expose computed `total_hours` and resolved customer name; require
  `gas_system_state` on any gas-carrying work-log entry; add the XLSX export
  behavior.

## Impact

- Code: `app/models/owned.py`, `app/services/` (repairs service), 
  `app/routes/api/` (repairs), `migrations/` (new revision).
- Contract: `docs/openapi.yaml` (remove `type`, add `delivery_date`,
  `total_hours`, customer name, export endpoint).
- Dependencies: add `openpyxl` to `requirements.txt`.
- Tests: `tests/` covering create/update/list/detail, gas-rule change, and the
  export endpoint; keep the migration round-trip test passing.
- The planned `frontend-repairs-ui` change depends on this contract and must be
  sequenced after it (`docs/openapi.yaml` → regenerate the frontend client).
