# Design

## Context

See `proposal.md` for the motivation. `app/services/repairs.py` decorates repair responses with raw elapsed hours from a batched work-log query. Excel uses that same list service. `end_data` already distinguishes active from archived repairs and can be cleared over the API. Work-log mutations and gas movements already share a route-level transaction. The settings service supplies workshop-wide weekday intervals, yearly holiday ranges, and operator names. Production uses SQL Server and dev/tests use SQLite.

## Goals / Non-Goals

**Goals:** Share one calendar calculator across live reads and archive writes, preserve historical values, and make both archive and timer handoff safe under concurrent requests.

**Non-Goals:** No second public time metric, per-operator calendar, automatic public-holiday lookup, timezone conversion, new reopening UI, or new authorization roles. Reuse the existing API reopen operation and permission model.

## Decisions

### Keep one public total and separate the snapshot from live values

Add a nullable persisted snapshot to `REPAIRS` (for example, `archived_total_hours`) and keep `total_hours` as the existing numeric response and workbook field. Active reads calculate, never write. When `end_data` transitions from null to non-null, check for running logs, compute once from the current settings and work logs, and commit the snapshot with the end date. On reopen, clear the snapshot and return the live total; a later archive takes a fresh snapshot. Updating an already-archived repair does not recompute the snapshot. A repair created with an end date, if accepted by an existing caller, has no logs and starts with a frozen zero.

A separate persistence field avoids accidentally persisting provisional values from the read-time decorator. Freezing the numeric result rather than the calendar is enough to guarantee a stable display without versioning settings. Whole-repair deletion retains its existing cascade and cylinder balance behavior; individual work-log changes require reopening first.

### Count local wall-clock intersections per work log

Read `working_hours` and `holidays` through the settings service, honoring its defaults, once per calculation batch. Normalize the weekday intervals into a union so overlapping settings cannot double count. Treat absent weekday keys in an explicitly saved schedule as closed. Treat vacations as inclusive whole-day exclusions keyed by the date's year. For each positive completed work-log interval, intersect it with the applicable daily windows, sum the covered seconds per repair, and convert to fractional hours. A running, missing-bound, zero-length, or reversed log contributes zero to adjusted totals. Do not round each log or de-duplicate time between operators. Retain the existing batched reads and cache normalized calendar data within the request, not across requests.

### Keep timer handoff and archive checks transactional

A running timer has a start time and no end time. On creation, validate the configured operator, payload, and gas changes before any handoff. For a new running log, find the same operator's running logs on active repairs and stop them at the submitted start time; reject the request if this would create a negative interval. Close matching legacy duplicates at the same boundary rather than choosing one arbitrarily. Neither a completed historical entry nor a date-less metadata entry triggers a handoff. Legacy archived running logs stay untouched; if their repair is reopened, those logs become active again.

Serialize archive/reopen and work-log writes that can affect a repair's archive check or a handoff. Use a database-backed transaction guard across these mutations: a single seeded guard row updated before reading relevant state is a simple cross-database option and also handles concurrent starts when there is no previous timer to lock. Acquire the guard before authoritative repair/log reads and hold it until commit or rollback. A process-local mutex would not cover multiple workers, and a row lock on the previous timer alone cannot cover the no-row case. Keep the existing gas movement in the same transaction. Unrelated operators are serialized briefly, which is a trade-off for a simple first version.

### Preserve legacy log data and update the API contract

Use a nullable text column for descriptions; preexisting rows need no rewrite. Require a configured operator on creation, not retroactively when editing a legacy row. Keep update input separate from create input in OpenAPI so stopping a log with an end-time-only update still works. Report archive conflicts through the existing error envelope with timer IDs and operator names when known. The repair UI keeps the Stop controls available after a conflict; the editor uses configured operator selection for new entries and still displays legacy operator values when editing.

## Risks / Trade-offs

- **Historical totals could drift during rollout.** Backfill using the old raw-duration behavior, including zero contribution for missing bounds, not the new calculator. Pause writes while taking the baseline so the snapshot reflects the data the old version reported.
- **Archive can race with a new or edited log.** Validate state after taking the transaction guard. Test both orderings: either the new timer commits first and archive is rejected, or archive commits first and the subsequent log write is rejected.
- **Existing clients may omit operators.** Keep the route and error envelope, document the new requirement, regenerate frontend types, and update callers and fixtures together.

## Migration Plan

Add the nullable snapshot and description fields and initialize any transaction-guard storage through Alembic. Backfill archived repairs only with the old elapsed-hours sum (zero for repairs without complete logs); leave active snapshots null and existing work logs unchanged. Run the migration and deploy the API and frontend together before resuming writes. Before accepting writes, verify that archived totals match a pre-upgrade sample. For rollback, retain additive data if possible; exporting snapshots and descriptions is necessary before any downgrade that drops those fields. An older application would display raw totals, not the new snapshots.
