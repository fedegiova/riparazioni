# Design

## Context

See `proposal.md` - Why. The read-only reference data already exists end to end:

- Backend `GET /api/v1/customers` and `GET /api/v1/vehicles` are implemented
  (`app/routes/api/reference.py`) and documented in `docs/openapi.yaml`; their
  response shapes are `Customer` and `Vehicle`.
- The frontend already exposes `listCustomers()` and `listVehicles()` in
  `frontend/src/api/reference.ts` and types in `frontend/src/api/types.ts`.
- `frontend/src/hooks/useApi.ts` provides loading/error/data state.
- `AppShell` already routes `/anagrafica` and shows its breadcrumb; only
  `frontend/src/pages/AnagraficaPage.tsx` is a placeholder.

So this is a frontend-only change with no API or data-model work.

## Goals / Non-Goals

**Goals:**
- A tabbed `/anagrafica` page listing customers and allestimenti, read-only.
- Reuse the existing reference-data helpers and loading hook.
- Loading, error, and empty states for each list.

**Non-Goals:**
- Any create/edit/delete, detail drill-down, or a users tab.
- Sorting or pagination (see Risks).
- Backend, OpenAPI, or database changes.

## Decisions

- **Two tabs, Clienti default.** Follow the existing `MagazzinoPage` pattern
  (`useState` tab index with MUI `Tabs`/`Tab`), so the page matches the
  warehouse screen's look and behavior. The request names only customers and
  allestimenti, so no users tab is added.
- **Load per tab on demand.** Mount a tab's list only when it is selected, as
  `MagazzinoPage` does. The shared `useApi` hook then fetches on mount, so the
  hidden tab is not requested. Alternative: load both eagerly - rejected
  because it makes a request the user may never look at.
- **Reuse `listCustomers`/`listVehicles` and `useApi`.** No new API layer.
  A small read-only table is written inline in the page; extract a shared
  component only if it keeps the page readable.
- **Single client-side search box per tab.** Filter the already-loaded rows in
  memory across the tab's visible columns, case-insensitively, showing all rows
  for an empty query. The list endpoints expose no query parameters, so there is
  no API change. Alternative: server-side search - rejected because it needs
  backend work and the lists are small enough to filter in the client.
- **Column selection.** Clienti: `cliente`, `via`, `cap`, `citta`, `prov`,
  `tel`, `cell`, `email`. Allestimenti: `targa`, `autocarro`, `carrozzeria`,
  `modello`, `classe`, `commessa`. These cover the identifying/contact fields
  users need; further fields (`note`, dates) can be added later without
  changing the spec.
- **Read-only by construction.** No actions column and no write helpers are
  imported, so the page cannot mutate reference data.

## Risks / Trade-offs

- [Legacy tables can be large and the endpoints return the full list] →
  Accepted for now; the page renders what the API returns and the search box
  filters it in memory. Server-side search or pagination is out of scope and can
  be added later without changing the listing behavior.
- [Blank/missing legacy fields (`cap`, `prov`, `targa`) may render empty
  cells] → Render an em dash or empty string for missing values so rows stay
  aligned.
- [Two list implementations may drift] → Keep the two tables small and
  structurally similar; extract a shared component if they grow.
