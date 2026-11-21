# Design

## Context

See `proposal.md` — Why. Constrains the approach:

- The equipment CRUD API for refrigerators, gas cylinders, and service parts
  already exists (`app/routes/api/equipment.py`, `app/models/owned.py`,
  `docs/openapi.yaml`), so the page is mostly a frontend build.
- Gas bookkeeping lives in `app/services/repairs.py` (`_validate_gas`,
  `_apply_gas`, `_restore_recharge`), which currently moves only the recharged
  weight and ignores the recovered weight.
- Known settings are a fixed registry in `app/services/settings.py`
  (`_DEFAULT_FACTORIES` + `_VALIDATORS`); a new named setting is added there.
- Migrations are Alembic over the owned tables only
  (`migrations/env.py` `include_object` filter): production is MSSQL, dev and
  tests are SQLite. Dev mode replays the real migration path.
- The frontend client is generated from `docs/openapi.yaml`
  (`npm run generate:api`) and committed; types come from the generated
  `components['schemas']`.

## Goals / Non-Goals

**Goals:**

- Manage spares and gas cylinders from the UI on top of the existing API.
- Give cylinders a real lifecycle: refill, archive, restore, and
  delete-if-unreferenced.
- Make the cylinder balance and the per-repair gas record mathematically
  correct (recovery adds, recharge subtracts, both stored independently).

**Non-Goals:**

- Picture upload for spares/cylinders (`picture_ref` stays a field).
- The refrigerators *equipment* tab (deferred).
- Recovery into a cylinder other than the entry's cylinder (modeled as a
  separate work-log entry).
- A full per-cylinder movement ledger UI; the balance plus the exchange
  records are the accounting surface.

## Decisions

### D1. Archive is a boolean `archived` column

`GAS_CYLINDERS.archived` mirrors the existing `SERVICE_PARTS.is_refrigerator_part`
boolean rather than introducing a status enum. Only two states are needed and
the transition is reversible; a status enum would add a state machine with no
consumer.

### D2. Archive gate: `remaining_weight < full_weight / 4`, checked at archive time

The backend rejects archiving at or above the threshold (400). `full_weight` is
therefore mandatory (D6). Restore never touches the balance. The list excludes
archived cylinders unless `?archived=true` is passed; archived cylinders are not
offered for recharge/recovery.

### D3. Delete stays a foreign-key concern; archive is the retire path

Deleting a referenced cylinder keeps relying on the existing FK +
`passive_deletes` → HTTP 409 (unchanged). A referenced cylinder can only be
retired by archiving. No new delete endpoint is needed.

### D4. Refills are their own table with reset-to-full semantics

New `REFILLS(id, gas_cylinder_id → GAS_CYLINDERS.id, date, reference)`.
Recording a refill sets `remaining_weight := full_weight` and `archived :=
false` in the same transaction. A cylinder goes out and comes back full, so no
added-weight column is stored (the amount is implicit: `full - remaining before`).
Alternative rejected: a `weight` column, which only pays off for partial
top-ups that this workshop does not perform.

### D5. Recovery lands in the entry's cylinder; both weights stored independently

`GAS_SYSTEM_STATES` gains `RECUPERO`. Validation becomes a field matrix rather
than today's `has_cylinder == has_weight`:

```
 state               cylinder   recharge        recovered
 VUOTO               required   required (>0)    forbidden
 PIENO               forbidden  forbidden       forbidden
 RECUPERO            required   forbidden       required (>=0)
 RICUPERO_RICARICA   required   required (>0)    required (>=0)
```

Balance effect per entry: `remaining += recovered - recharged`. A movement that
goes below 0 or above `full_weight` is rejected (400) in the same validation
pass. Update and delete reverse both movements symmetrically
(`remaining += recharged - recovered`), replacing `_restore_recharge` usage in
`delete_repair` and `update_work_log_entry`.

### D6. `full_weight` becomes required via a new revision

Column is currently nullable; D2 and the balance math need it. A new append-only
revision sets it NOT NULL. The database is empty, so there is no backfill — the
tighten is emitted through `op.batch_alter_table` (SQLite cannot `ALTER COLUMN`;
batch is a passthrough on MSSQL). Create/update reject a missing `full_weight`
(400). The migrations are folded into a single baseline once development is
complete.

### D7. `gas_types` is a plain string list, enforced only in the UI

Registered in `settings.py` like `operators` (default `[]`, validator
"list of non-empty strings"). The cylinder form renders a picker from it; the
backend does not validate `cylinder.gas_kind` against it, so legacy and
newly-named kinds keep working.

### D8. Frontend: one shared parts screen, a tabbed shell

`MagazzinoPage` becomes the tab host (MUI `Tabs`): Ricambi, Ricambi Frigo,
Bombole. Ricambi and Ricambi Frigo render the same `PartsManager` component
parameterized by `is_refrigerator_part` (the flag only selects the list and
sets the flag on create). A `CylindersManager` renders the overview, the list
with a fill indicator, and the refill/archive/restore/delete actions. The
generated client is refreshed from the updated OpenAPI document.

### D9. Gas-used summary is a read-time computed field

Like `total_hours`/`customer_name`, the service attaches `gas_used` (sum of
recharged weights of a repair's entries) at read time; it is added to the
repair detail and to the Excel export columns. No storage changes.

## Risks / Trade-offs

- **[Tightening `full_weight` and the gas matrix is a breaking API change]** →
  Clients creating a cylinder without `full_weight`, or entries that previously
  passed, now get 400. Mitigation: documented as **BREAKING** in the proposal;
  update `docs/openapi.yaml`, the contract test, and existing equipment tests.
- **[Default cylinder list now hides archived rows]** → Any caller assuming the
  full set shrinks. Mitigation: `?archived=true` opt-in and updated tests.
- **[SQLite cannot `ALTER COLUMN`]** → The `full_weight` NOT NULL tighten must be
  emitted with `op.batch_alter_table` (a passthrough on MSSQL). With an empty
  database there is no data copy or inbound-FK risk, so the rebuild is trivial.
  Mitigation: dev mode replays the real migration on SQLite; verify the MSSQL
  branch at deploy.

## Migration Plan

1. New Alembic revision (revises `75d9543863f9`): create `REFILLS`; add
   `GAS_CYLINDERS.archived` with a `0` server default; tighten `full_weight` to
   NOT NULL with `batch_alter_table`. No backfill — the database is empty.
2. `alembic upgrade head` on MSSQL; `make dev-init` / `flask dev-init` replays
   it for dev. Rollback: `downgrade` drops `REFILLS` and `archived` and relaxes
   `full_weight` (batch again on SQLite).
3. Update `docs/openapi.yaml` (archive/restore/refill paths, `archived` field,
   `RECUPERO` enum, `gas_used`), regenerate the frontend client.
4. Deploy backend first (additive except the two breaking tightenings), then the
   frontend.

## Open Questions

- Exact rendering of the cylinder overview summary (counts by state vs. a fill
  histogram) — cosmetic, can settle during UI work.
- Whether the refill `reference` should be rendered as required in the form even
  though the API stores it as an optional string.
