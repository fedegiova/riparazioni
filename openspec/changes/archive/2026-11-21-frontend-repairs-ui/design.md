# Design

## Context

See `proposal.md` - Why. Relevant current state: the frontend is a shell
(`frontend/src/App.tsx`) with a single `AppBar`, a `HomePage` and
`NotFoundPage`, MUI theming in `theme.ts`, and a typed `openapi-fetch` client in
`api/client.ts` generated from `docs/openapi.yaml`. There is no data-fetching
library, no component library beyond MUI, and no router layout beyond a single
`BrowserRouter`.

This change depends on `repairs-api-delivery-and-export` (it consumes
`delivery_date`, `total_hours`, the resolved customer name, and the export
endpoint) and must run after that change and a client regeneration.

## Goals / Non-Goals

**Goals:**
- A tablet-first shell with breadcrumb, bottom navigation, and a home control.
- The landing (active repairs), repairs list (all + search + delete + export),
  repair page (fields, parts, work log, archive), and work-log editor.
- Reuse of the shared, generated API client for all data access.

**Non-Goals:**
- Implementing the Magazzino, Anagrafica, or Ricambi screens (placeholders only).
- Any backend/API change (handled by the dependency change).
- Authentication or offline support.

## Decisions

**1. Route map.** `/` landing, `/repairs` list, `/repairs/new`,
`/repairs/:id` edit, `/repairs/:id/work-log/:entryId` work-log editor, with
`/magazzino` and `/anagrafica` as placeholder routes. Breadcrumbs are derived
from the active route; the bottom navigation highlights the matching section.
Alternative (modal-based editing) rejected: the brief calls for dedicated pages
and a work-log route.

**2. Bottom navigation is shown on the three top-level sections and hidden on
the repair/work-log editor pages.** The editors are drill-downs that need the
vertical space for a tablet form. Alternative (always-visible nav) rejected for
crowding the editors.

**3. A reusable search-modal component drives reference picking, filtering client-side.** A single dialog loads a reference list (customers or vehicles) once, caches it in memory, and filters it client-side as the user types (debounced), rendering at most ~50 matches with a "refine your search" hint before returning the selection to the field. The rendered cap keeps a multi-thousand-row list out of the DOM and the cache avoids a refetch on every open. Alternatives: a native `<select>` or MUI `Select` (rejected — enumerating or scrolling ~3000 rows with no search is unusable on a tablet); inline `Autocomplete` (viable, but the brief asks for a modal and it gives larger touch targets); server-side search (deferred — see Risks).

**4. Data access via the shared client with a small custom hook.** A lightweight
`useApi`-style hook wraps the generated client for loading/error state. A
data-fetching library (e.g. TanStack Query) was considered but rejected to avoid
a new dependency for this scope; revisit if caching needs grow.

**5. Parts are edited as a full set.** Because `PUT /repairs/{id}` replaces the
`parts` array when present, the Parts table keeps local state authoritative and
saves the whole array on change. Alternative (per-part endpoints) rejected:
there are none.

**6. Archive and delete reuse existing endpoints.** Archive sets `end_data` via
`PUT`; delete uses `DELETE /repairs/{id}` behind an MUI confirmation dialog.
Export links the browser to `GET /api/v1/repairs/export` with the current query
string rather than fetching into memory.

## Risks / Trade-offs

- **Large reference lists.** The customer list is ~3000 rows and the reference
  endpoints expose no search filter. → Client-side filtering with a capped
  result set and an in-memory cache is comfortably sufficient at this size, and
  the dataset is not expected to grow by an order of magnitude in the
  foreseeable future. If it ever does, add a `search` parameter to the
  reference endpoints in a follow-up change.
- **Sequencing**: the UI does not compile against the old contract. → Land the
  backend change and regenerate the client before starting the UI pages.
- **Tablet usability**: generic MUI table density can be too small for touch. →
  Use larger row heights and touch-sized action buttons on the tables.
- **No auth**: the app assumes a trusted workshop device. → Out of scope; note it.

## Migration Plan

No data migration. Deploy the dependency change first, regenerate the frontend
client, then ship the UI. Rollback is reverting the frontend deploy.
