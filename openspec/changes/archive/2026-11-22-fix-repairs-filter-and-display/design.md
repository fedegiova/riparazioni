# Design

## Context

See proposal.md — Why. The relevant current state:

- `app/services/repairs.py::list_repairs` parses `start_date_from`/`start_date_to`
  with `datetime.fromisoformat` and compares with `>=` / `<=`. A date-only
  `start_date_to` (`YYYY-MM-DD`) becomes midnight at the **start** of that day.
  The export route reuses `list_repairs`, so it shares the defect.
- The frontend date inputs send date-only strings (`frontend/src/pages/RepairsListPage.tsx`).
- The repair detail payload carries only the `vehicle` id (no resolved label);
  `RepairPage` seeds the Targa field as `#<id>` and never looks up the plate.
  The reference API already exposes `GET /api/v1/vehicles/{id}`.
- `RepairsListPage` and `HomePage` render the "End date" cell from
  `repair.delivery_date`. `end_data` (the actual close time) and `delivery_date`
  (the customer's requested date) are distinct API fields.

## Goals / Non-Goals

**Goals:**

- A date-only `start_date_to` includes the whole selected day, while a full
  datetime upper bound keeps its exact `<=` semantics.
- The repair page shows a loaded repair's plate, falling back to `#id` only when
  the lookup fails.
- The repairs list shows delivery and end dates as separate, correctly labelled
  columns; the landing labels its delivery-date column correctly.

**Non-Goals:**

- Adding a resolved vehicle label to the repair payload (an API shape change):
  the existing per-id lookup is enough for the detail page and keeps the
  contract unchanged.
- Changing the `start_date_from` lower bound: `>=` midnight already includes the
  whole first day.
- Any change to the OpenAPI document or generated client.

## Decisions

**Date-only upper bound uses a half-open comparison.**
When the raw `start_date_to` value is a date with no time, compare with
`start_data < start_to + timedelta(days=1)`; a value carrying a time keeps
`start_data <= start_to`. This includes every instant on the selected day
without special-casing the final second/microsecond. The date-only test is a
strict `YYYY-MM-DD` string check (a `datetime.fromisoformat` of a full datetime
must not be treated as a whole-day bound).

**Resolve the plate with the existing reference endpoint.**
`RepairPage` seeds the Targa field from the repair's `vehicle` id, then calls a
new `getVehicle(id)` (`GET /api/v1/vehicles/{vehicle_id}`) and updates the label
to the plate. The state update is guarded by a functional setter that only
applies while the field still holds the same id, so a vehicle chosen from the
search modal in the meantime is not overwritten. The `#id` fallback covers a
failed or missing lookup. This avoids changing the repairs API/spec for a
display-only concern.

**Separate the two date columns instead of choosing one.**
The list page shows `delivery_date` under **Delivery date** and `end_data` under
**End date**. The landing page, which lists only open repairs, relabels its
single date column **Delivery date** (an "End date" there would always be
empty). `formatDate` already trims a datetime to its date part.

## Risks / Trade-offs

- [The vehicle lookup is an extra request per loaded repair] → It is a single
  small lookup, skipped when the repair has no vehicle, and the fallback renders
  immediately.
- [A lookup that resolves after the user changes the vehicle could overwrite the
  choice] → The functional setter only applies while the id still matches the
  loaded repair.
- [Existing rows with `start_data` at exactly the next midnight] → The half-open
  bound excludes midnight of the following day, which is correct: it is no
  longer the selected day.

## Migration Plan

No schema or API change; frontend behavior plus one backend comparison. Deploy
as usual; rollback is reverting the commit.
