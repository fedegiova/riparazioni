# Tasks

## 1. Storage and migration

- [x] 1.1 Add the repair snapshot, nullable work-log description, and transaction guard storage to the models and Alembic. Verify migration from the preceding revision preserves current archived raw totals (including zero), leaves active snapshots unset, and does not modify existing work logs. Check SQLite and the production SQL Server dialect.

## 2. Calendar calculation and repair lifecycle

- [x] 2.1 Implement the shared local-calendar calculator and wire it into live list/detail totals and Excel export. Add tests for default and custom schedules, split and overlapping intervals, closed days, inclusive vacations across a year boundary, incomplete/reversed logs, overlapping operators, and list/detail/export agreement. Update the `total_hours` documentation.
- [x] 2.2 Wire the transaction guard into archive/reopen and relevant repair and work-log writes. Implement archive rejection with blocker details, snapshot persistence, reopening and re-archiving, and protection against individual archived work-log mutations. Document the conflict responses and test archive retry after an explicit stop, live calendar corrections, archived stability after calendar and metadata edits, and preserved gas/cascade behavior.

## 3. Work-log API

- [x] 3.1 Expose description on work-log reads, creates and updates; enforce configured operator selection on creation. Separate create and partial-update OpenAPI inputs and regenerate frontend types. Verify description round-tripping, omitted/unknown operator rejection, and end-time-only updates for legacy entries. Update existing repair and gas test fixtures to send a configured operator on creation.
- [x] 3.2 Implement the guarded same-operator handoff at the new start time. Document the handoff in the API and add tests for same- and cross-repair starts, unaffected operators, historical and date-less entries, backdated rejection, and rollback when gas validation fails.

## 4. Workshop UI

- [x] 4.1 Update `WorkLogPage.tsx` with the optional description and required configured operator selection for new logs. Verify the selected operator and description are submitted, no creation is possible without a valid selection, an empty or unavailable list is explained, and a legacy entry can still be edited.
- [x] 4.2 Update `RepairPage.tsx` to show descriptions, hide mutation controls for archived work logs, and show actionable timer blockers when archiving fails. Verify the manager can explicitly stop timers and retry, and that archived work logs remain visible without mutation controls.

## 5. Integration verification

- [x] 5.1 Use independent transactions to verify two starts for the same operator cannot leave duplicate running timers, and verify there is no successful archive with a running timer when archive and start race. Run the repair, settings, gas and migration regression tests and the frontend test suite and build.
