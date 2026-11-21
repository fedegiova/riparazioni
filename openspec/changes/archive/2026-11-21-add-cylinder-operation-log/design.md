# Design

## Context

See proposal.md - Why. The application already stores everything the log needs:
`REFILLS` (date + free-text reference, owned by the cylinder) and
`REPAIR_WORK_LOG` (a nullable `gas_recharge` foreign key to the cylinder plus
`gas_system_state`, `gas_recharge_weight`, `gas_recovered_weight`, `operator`,
`start_time`/`end_time`). Cylinder routes live in `app/routes/api/equipment.py`;
the frontend warehouse screen is `frontend/src/components/CylindersManager.tsx`
inside the `/magazzino` page, and the API client is generated from
`docs/openapi.yaml`. No model or migration work is required — this change reads
existing rows.

## Goals / Non-Goals

**Goals:**
- Serve one merged, newest-first operation log per cylinder with source
  references, from existing data.
- Give the workshop a per-cylinder page reachable from the Bombole tab.

**Non-Goals:**
- Auditing cylinder field edits, creation, archive, or restore (only
  gas-affecting operations, per the clarified scope).
- Persisting a new operation/audit table — the running balance is computed, not
  stored.
- Editing the balance outside refills and gas movements (the edit path is closed
  off instead).

## Decisions

### Derived log, not a new table
Build the log on read by concatenating the cylinder's `refills` relationship
with the `RepairWorkLog` rows whose `gas_recharge` equals the cylinder id, then
sorting. Alternative — a persisted `CYLINDER_OPERATIONS` table written on every
movement — was rejected: it duplicates data the work log already holds, needs a
backfill for existing cylinders, and would drift from the work-log balances.
Only gas-affecting operations are in scope, so they are all reconstructable.

### `GET /api/v1/gas-cylinders/{cylinder_id}/operations` returns a flat array
Mirrors the existing `/refills` sub-resource (array of entries, ascending there;
this one newest-first as required). The page fetches the cylinder separately via
`GET /api/v1/gas-cylinders/{id}` for identity/state, so the operations payload
stays a plain list. A cylinder with no operations returns `[]`; an unknown id
returns 404 via the existing `_get_or_404` helper.

Entry shape (discriminated by `kind`):
- `{"kind": "refill", "id", "date", "reference"}` — from a `Refill`.
- `{"kind": "recharge" | "recovery" | "recovery_recharge", "date",
  "repair_id", "work_log_id", "operator", "gas_system_state",
  "recharged_weight", "recovered_weight"}` — from a `RepairWorkLog`; `kind` is
  derived from `gas_system_state` (VUOTO→recharge, RECUPERO→recovery,
  RICUPERO_RICARICA→recovery_recharge). `PIENO` never references a cylinder, so
  it never appears.

### Ordering
Sort all entries by operation time, newest first. A refill contributes its
`date` (midnight); a movement contributes `start_time` (falling back to
`end_time`, then id) so refills and movements interleave correctly. Stable
tie-break by kind then id keeps the order deterministic for tests.

### Running remaining weight
Each entry also reports the cylinder's balance *after* that operation. Compute it
by replaying the log oldest-first from a starting balance of the cylinder's
`full_weight` at creation: a recharge subtracts `recharged_weight`, a recovery
adds `recovered_weight`, a combined operation applies both, and a refill resets
to `full_weight`. The same deterministic sort is used ascending for the replay,
then reversed for display, so a row's balance always matches its position. The
balance is computed, never stored (see proposal - the log is the source of
truth).

### Balance is read-only after creation
Because the running balance is reconstructed from the log, any balance change
outside the log would make the reconstruction disagree with the cylinder. The
update endpoint rejects `remaining_weight` (400). The cylinder editor keeps an
editable remaining-weight (initial balance) field on the create form — so a
partly-full cylinder can be registered — and renders that field read-only
(disabled) when editing an existing cylinder; the update payload never carries
`remaining_weight`. After creation the balance therefore moves only through
refills and gas movements.

### Client-only limit on the initial balance
The create form also refuses a remaining weight above the full weight before
calling the API. This lives in the client only, by request: the update path
already forbids balance changes, and the API keeps accepting any non-null
initial balance at creation, so no server-side check is added.

### Implementation location
Follow the current route-per-resource style in `app/routes/api/equipment.py`
(the equipment domain has no service module yet). Extract the merge-and-sort into
a small module-level helper so it is unit-testable and the route stays thin; no
service package is introduced just for this.

### Frontend page and navigation
Add `frontend/src/pages/CylinderPage.tsx` at route `/magazzino/bombole/:id`
(registered in `frontend/src/App.tsx`), reusing the `useApi` hook to load the
cylinder and its operations. `CylindersManager` gains a per-row log control
(icon button) that navigates with react-router. Movement entries link to
`/repairs/:repair_id` (and the work log where useful); refill entries render the
reference text. Add a thin wrapper (`getCylinderOperations`) in
`frontend/src/api/equipment.ts`; the OpenAPI addition + regenerated client cover
the types.

## Risks / Trade-offs

- [Refills only store a date, so a refill and a same-day movement order by
  time-of-day assumptions] → Sort ties deterministically and treat a refill as
  start-of-day; the newest-first requirement is still met for distinct times.
- [The running balance assumes the cylinder started full at creation] → The
  creation form no longer sets a partial balance; a cylinder seeded with a
  non-full initial weight through the API is replayed from full, so its earliest
  rows are approximate (exact again from the first refill onward).
- [Legacy manual balance edits are not in the log] → Balances edited before this
  change may make the reconstruction disagree with the stored weight; the edit
  path is now closed so it cannot drift further.
- [Deleting a work-log entry reverses the balance and removes it from the log]
  → Consistent with the existing model (the operation no longer happened); noted
  so the log is understood as current truth, not an immutable audit trail.
