# Design

## Context

See `proposal.md` for the motivation. `REFRIGERATORS` and its CRUD API already store `serial_nr`, `brand`, `model`, `gas_kg` and notes. `REPAIRS` already has a refrigerator foreign key and a service-validated reference to legacy `TBALLESTIMENTI.ID_INT`. The repository still defines gas system states, but there is no deployed gas state to carry forward. Work-log writes and repair changes use a database-backed transaction guard for timer handoff and archival.

## Goals / Non-Goals

**Goals:** Reuse the catalog and reporting model; make refrigerator identity, measurement origin, and inventory changes explicit; apply the same validation through the API and UI.

**Non-Goals:** Do not alter legacy reference tables, migrate old gas entries, support two gas models, introduce multi-cylinder movements, or add a regulatory submission workflow.

## Decisions

### Store the current installation on the app-owned refrigerator

Add nullable `allestimento_id` and `gas_kind` to `REFRIGERATORS`. Reuse `serial_nr`, `brand` (displayed as Manufacturer), `model` and `gas_kg` (displayed as Nameplate capacity, kg) rather than duplicating or renaming them. A unique filtered/partial index on non-null allestimento IDs enforces one current installation on SQL Server and SQLite while allowing multiple uninstalled records. Validate the external ID through the service, as repairs do; do not modify or add an FK to the legacy table. Validate complete nameplate details for installations and use the existing `gas_types` setting for new or changed refrigerator gas types. Existing uninstalled rows may remain incomplete.

Use an explicit replacement action that detaches the old unit and installs a new or already registered uninstalled unit atomically. A plain create against an occupied allestimento conflicts, and an installed record cannot be deleted. This keeps a current link and preserves repair references without adding a full installation-history table. Anagrafica joins installations by identifier in bulk; it distinguishes failed refrigerator data loads from vehicles that genuinely have no unit.

### Lock the repair at the first successful new gas write

Store an explicit lock (for example, `gas_equipment_locked`) rather than treating a non-null `REPAIRS.refrigerator` as locked: callers can already set that field before gas work exists. On a first valid gas write, resolve the current installation from the repair's vehicle, set the existing refrigerator FK to that unit, and set the lock. No separate refrigerator selection is required on the repair. Until then, retain existing optional repair references for compatibility. After locking, reject changing or clearing the vehicle or refrigerator, even if gas work is later removed or the repair is reopened. Expose both the historical unit and current installation status in repair detail so the editor can explain when a separate repair is needed.

Check the installation at save time. The editor should send the expected refrigerator ID it displayed so that an installation changed after the editor loaded is rejected rather than silently bound to the replacement. Unrelated work-log edits and reversal of recorded movements do not depend on the current installation, type, or nameplate. Use the existing transaction guard for installation changes, gas-work writes, and repair reassignment, and coordinate concurrent cylinder balance writes (including refills) under the same transaction discipline. Acquire it before reading authoritative installation and balance values. Validate before applying any timer handoff or lock.

### Keep measured inputs distinct from gross and net stock effects

Use `gas_operation` (`none`, `fill`, `recovery`, `recovery_recharge`) as the only operation discriminator. Persist a cylinder reference, one measured mass in kg (`gas_measured_kg`), and the nameplate capacity used for combined work. The operation tells the editor whether that mass means added, recovered, or net added. Treat pre-change work logs without a new operation as ordinary work. Remove the old state enum, payload handling, and replay branches rather than translating them. Validate finite numbers and use consistent precision for balances and reversals.

For a combined entry with saved nameplate `C` and measured net addition `N`, derive gross recharge `C` and calculated recovery `C - N` from those two values. Apply cylinder delta `-N` once; there is no intermediate balance to validate. Treat zero as a real input, not a blank. Fill subtracts its entered amount; recovery credits its measured amount. Reject missing or unequal gas kinds and movements outside cylinder stock limits.

Use one movement calculation for live accounting, reversal, history replay, and reporting. On update, omitting gas fields preserves the movement; explicitly submitting `none` clears and reverses it. Validate replacements against the balance after undoing the saved movement. The warehouse labels calculated recovery and displays measured net addition. `gas_used` remains gross recharged weight in the API and Excel export.

## Risks / Trade-offs

- **Nameplate math is an estimate of recovery.** Label the derived quantity as calculated in the work log and cylinder history; persist the nameplate used so master-data edits cannot change past results.
- **The repository and deployed schema may differ.** Inspect the deployed schema before rollout; do not make the new logic or migration depend on the presence of obsolete gas columns. Update OpenAPI and deploy the API and UI together.
- **Concurrent replacements or balance updates could misattribute a job or lose a stock movement.** Use the transaction guard, database uniqueness for installations, and server-side revalidation; integration tests should exercise stale selections and concurrent writes.
- **The existing replay reconstructs balances from historical entries.** Retain existing initialization/refill behavior rather than attempting to reconcile unrelated historical discrepancies in this change. Verify the new combined delta against a known opening balance.

## Migration Plan

Verify the deployed work-log schema before applying the migration. Add the new catalog and work-log fields, the filtered unique index, and a repair lock defaulting to false. If obsolete gas columns exist, leave them unused; the migration must not require them. Test upgrade on SQLite and the SQL Server dialect. Do not backfill gas entries or rewrite ordinary work logs, cylinder balances, or repair links. Register installations through Anagrafica as needed; the gate applies to gas work, not ordinary work.

Deploy schema, then switch the API and UI together before taking new gas writes. A rollback before new entries may remove the additions; after new-style entries exist, preserve or export the new lock, installation, and movement data before any downgrade, and pause gas writes rather than run the old UI against unsupported new records.
