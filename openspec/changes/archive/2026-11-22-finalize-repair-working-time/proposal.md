# Proposal

## Why

Repair totals currently include time outside the workshop schedule and during vacations. Managers need to see the corrected total while work is ongoing, then finalize it without future calendar edits rewriting archived records. They also need clear work-log notes and a reliable way for operators to switch timers between repairs.

## What Changes

- Calculate the existing `total_hours` on the server for active repairs by summing the portions of completed work logs that fall within configured working hours and outside vacation dates. Use the same value in repair responses and Excel export.
- Require the manager to stop all running timers before archiving. Save and freeze the adjusted total on archive, preserve existing archived totals at rollout, and return to live calculation on explicit reopen.
- Add an optional text description to work logs and expose it in the editor and work-log table.
- **BREAKING**: Require a configured operator when creating a work log. Starting a new timer for that operator stops their previous timer at the new start time, even on a different active repair. Recording completed historical work does not stop a timer.
- **BREAKING**: Reject work-log changes while a repair is archived; reopen the repair to correct its logs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `repairs`: Calendar-adjusted and frozen totals, archive/reopen rules, operator timer handoff, and work-log descriptions.
- `repairs-ui`: Operator selection, work-log descriptions, and feedback when running timers prevent archiving.

## Impact

- Repair and work-log services, serializers, and Alembic migration for stored totals and descriptions.
- Existing settings supply the calendar; no change to their schema or editor.
- Repair and work-log API contracts, OpenAPI documentation and generated types, repair and work-log pages, and API/migration/UI regression tests.
