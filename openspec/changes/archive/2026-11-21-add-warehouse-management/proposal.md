# Proposal

## Why

The Magazzino page is a placeholder: spares and gas cylinders can be read
through the API but cannot be managed from the application. At the same time,
gas-cylinder balances and the per-repair gas record — the basis for the
regulatory report of how much gas each repair consumed — are not correct:
recovered gas is currently discarded from the balance, cylinders have no
lifecycle past "empty", and there is no way to record a refill. This change
delivers the warehouse screens on top of the existing equipment API and fixes
the gas accounting so that the cylinder balance and the gas-usage record are
auditable.

## What Changes

- Build the `/magazzino` page with tabs: **Ricambi** (spares,
  `is_refrigerator_part = false`), **Ricambi Frigo** (same management screen,
  `is_refrigerator_part = true`), and **Bombole** (gas cylinders).
- Full CRUD from the UI for spares and gas cylinders, using the existing
  `/api/v1/service-parts` and `/api/v1/gas-cylinders` endpoints.
- Cylinder overview: counts by state and a list showing each cylinder's fill
  level, with per-row refill / archive / restore / delete actions.
- **Archive** a gas cylinder when its remaining weight is below one quarter of
  its full weight. Archiving is reversible; restoring a cylinder keeps its
  current balance. Archived cylinders are hidden from the default list and
  shown via a toggle.
- **Delete** a cylinder only when no work-log entry references it; a
  referenced cylinder can only be archived.
- New **`REFILLS`** table and API: a refill (cylinder, date, reference)
  restores the cylinder to its full weight and unarchives it. Refills are
  allowed on any cylinder, including one that still holds gas.
- New **`gas_types`** setting (a list of strings, like `operators`) that feeds
  the cylinder form's gas-type picker; the settings page gains an editor for it.
- **BREAKING**: `full_weight` becomes required on gas cylinders (currently
  nullable). The archive threshold and every balance computation depend on it.
- **BREAKING**: correct the gas accounting. Recovered weight increases a
  cylinder's balance and recharged weight decreases it; both are stored as
  independent values (never collapsed to a delta). Add a `RECUPERO` gas-system
  state for recover-without-recharge (dismantling a failed unit), so a
  recovery can be recorded on the cylinder without inventing a recharge.
- (Nice-to-have) surface the gas used per repair as a summary on the repair
  detail and as an export column.

## Capabilities

### New Capabilities
- `warehouse-ui`: the warehouse page — its tabs, the shared spare management
  screen used for both regular and refrigerator parts, the gas-cylinder list
  with its state overview, and the refill/archive/restore/delete controls.

### Modified Capabilities
- `equipment`: gas cylinders gain an archived lifecycle, a required
  `full_weight`, and refill records; delete-vs-archive rules for cylinders.
- `repairs`: corrected gas accounting (recovered weight increases the
  balance), the new `RECUPERO` state, and the recover/recharge validation
  matrix.
- `settings`: add the `gas_types` known setting.
- `settings-ui`: add the gas-type list editor.

## Impact

- Backend: `app/models/owned.py` (`GAS_CYLINDERS.archived`, `full_weight`
  non-null, new `REFILLS` model), a new Alembic migration,
  `app/routes/api/equipment.py` (archive/refill endpoints, `full_weight`
  validation), `app/services/repairs.py` (recovery accounting, `RECUPERO`
  state, reversal on update/delete), `app/services/settings.py` (`gas_types`).
- API contract: `docs/openapi.yaml` (archive/refill paths, updated cylinder
  schema, `RECUPERO` enum).
- Frontend: `frontend/src/pages/MagazzinoPage.tsx` (replaces the placeholder),
  `frontend/src/api/equipment.ts` and `settings.ts` (create/update/delete and
  settings wrappers), generated client types, `frontend/src/pages/SettingsPage.tsx`
  (gas-type editor).
- Tests: `tests/test_api_equipment.py`, `tests/test_api_repairs.py`,
  `tests/test_api_settings.py`, frontend page/api tests, OpenAPI contract test.
