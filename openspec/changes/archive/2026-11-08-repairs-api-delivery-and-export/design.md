# Design

## Context

See `proposal.md` - Why. The relevant current state:

- `REPAIRS` columns: `id, customer, vehicle, start_data, end_data, type, notes, refrigerator`.
- Work-log durations live in `REPAIR_WORK_LOG(start_time, end_time)`; entries may have
  either timestamp null.
- The repairs **list** endpoint intentionally returns summary form (no `work_log`/`parts`).
- `customer`/`vehicle` reference the read-only external `DATIDBSTORICO` objects
  (`VICLIENTI` view, `TBALLESTIMENTI`) with **no DB foreign key**; integrity is
  validated in the service layer. Tests run on SQLite with an attached
  `DATIDBSTORICO` shim, and migrations must never touch external objects.

## Goals / Non-Goals

**Goals:**
- Expose `delivery_date`, computed `total_hours`, and resolved `customer_name` on repairs.
- Remove `type` cleanly across model, API, OpenAPI, and spec.
- Generalize the gas-state rule so it no longer depends on `type`.
- Serve a real `.xlsx` export of the (filterable) repairs list.

**Non-Goals:**
- Any UI work (separate `frontend-repairs-ui` change).
- Work-log spares, refrigerator semantics, or part-level changes.
- Storing `total_hours` or `customer_name` (both computed on read).

## Decisions

**1. `delivery_date` is a new nullable `Date`, distinct from `end_data`.**
`delivery_date` is the date requested by the customer; `end_data` is the actual
close timestamp. Alternative (repurpose `end_data` as the delivery date) was
rejected: the two genuinely differ (a repair can be closed after the promised
date, or promised for the future). Stored as a date (no meaningful time of day),
exposed in the API as `format: date`.

**2. Remove `type` rather than keep it nullable.**
The UI never surfaces it and gas handling can be decoupled from it, so a nullable
`type` would be dead weight. The gas rule becomes: any work-log entry carrying gas
data requires `gas_system_state`. Alternatives considered: defaulting `type` to
`RIPA` (rejected - hides a meaningless field) and leaving it required (rejected -
blocks the UI).

**3. `total_hours` is computed on read, in the list query.**
A single aggregate over `REPAIR_WORK_LOG` per repair (sum of
`end_time - start_time`, treating entries with a missing start or end as zero)
avoids a stored column that every work-log write path would have to maintain and
that could drift. Alternative (stored `total_hours`) rejected for that reason.
Returned as fractional hours, formatted by the UI.

**4. `customer_name` is resolved server-side.**
Resolve names for the distinct customer ids present in the response (one lookup
per distinct id, not per row) through the same external-reference access path the
create/update validation already uses, so it works against MSSQL and the test
shim alike. Alternative (client-side join against `/customers`) rejected because
the frontend should not have to stitch the list together.

**5. Export uses `openpyxl` over a dedicated endpoint.**
A new `GET /api/v1/repairs/export` reuses the list filters and writes a workbook
streamed as a download with the Excel content type. `openpyxl` is added as a
runtime dependency. Alternative (`/customers`-style CSV renamed `.xls`) rejected:
it is not a real workbook.

**6. One migration revision.**
A single Alembic revision drops `REPAIRS.type` and adds `REPAIRS.delivery_date`,
with a downgrade that re-adds `type` as nullable and drops `delivery_date`.

## Risks / Trade-offs

- **Dropping `type` is breaking.** Clients sending `type` must be updated. → Sequence
  the `frontend-repairs-ui` change after this one and note the removal in the API docs.
- **External customer resolution in two databases** (MSSQL vs. SQLite shim). → Reuse
  the existing external-query abstraction and cover it with shim-based tests.
- **Null-duration work-log entries** would contribute zero, so an open repair can show
  `0` hours. → Accepted; the UI presents a blank/zero consistently.
- **New dependency (`openpyxl`).** → Add to `requirements.txt`; CI installs runtime deps.

## Migration Plan

1. `alembic upgrade head` applies the revision (drop `type`, add `delivery_date`).
2. No backfill: `delivery_date` starts null for existing repairs.
3. Rollback: `alembic downgrade` re-adds `type` (nullable; prior values are lost) and
   drops `delivery_date`.

## Open Questions

- Exact `total_hours` serialization (fractional hours vs. seconds) can be settled during
  implementation without changing the specs, provided the value is numeric.
