# Proposal

## Why

The Anagrafica section is reachable from the app shell's bottom navigation, but
its page is only a placeholder: it says the master-data screens are "planned as
a follow-up change". Workshop staff therefore cannot look up the customers and
allestimenti (vehicles) that repair records reference, even though the read-only
backend endpoints for both already exist.

## What Changes

- Replace the placeholder `AnagraficaPage` with a **tabbed page at
  `/anagrafica`** offering a **Clienti** tab and an **Allestimenti** tab, with
  Clienti selected by default.
- **Clienti tab**: list the customers from the existing read-only
  `GET /api/v1/customers` reference data (name, address, contact fields).
- **Allestimenti tab**: list the vehicles from the existing read-only
  `GET /api/v1/vehicles` reference data (license plate, vehicle, body, model,
  class, and related fields).
- Give **each tab a single search box** that filters the loaded rows
  client-side across the tab's visible columns (case-insensitive), without
  changing the read-only data source.
- Load each tab's data on demand and show loading, error, and empty states.
- The page is **read-only**: no create, edit, or delete controls, and no write
  calls.
- Reuse the existing `listCustomers` and `listVehicles` helpers and the shared
  `useApi` loading hook; no backend, API-contract, or dependency changes.

## Capabilities

### New Capabilities
- `anagrafica-ui`: the read-only Anagrafica page that lists the legacy customer
  and allestimenti master data in a tabbed view.

### Modified Capabilities
<!-- None: the backend reference-data endpoints and the app shell already exist
     and their requirements are unchanged. -->

## Impact

- Frontend: `frontend/src/pages/AnagraficaPage.tsx` (tabs plus read-only
  customer and allestimenti tables and a per-tab search box), reusing
  `frontend/src/api/reference.ts` (`listCustomers`, `listVehicles`) and
  `frontend/src/hooks/useApi.ts`. A small read-only table component may be
  extracted under `frontend/src/components/` if it keeps the page readable.
- Tests: a new `frontend/src/pages/AnagraficaPage.test.tsx` covering the tabs,
  both lists, the error states, and the per-tab search filtering.
- No backend, `docs/openapi.yaml`, database, or dependency changes: the
  `reference-data` endpoints are already implemented and consumed.
