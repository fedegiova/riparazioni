# frontend

React web app for the riparazioni repair-management system: Vite +
React 19 + TypeScript + MUI. It consumes the Flask backend's `/api/v1`
API; see the [root README](../README.md) for the backend and
[`docs/openapi.yaml`](../docs/openapi.yaml) for the API contract.

## Prerequisites

- Node 22+ and npm
- For API calls, the backend running locally: `make install-dev` (first
  time) and `make run` (Flask on `127.0.0.1:5000`) at the repo root. The
  app shell renders fine without the backend.

## Setup

```bash
npm install
```

## Scripts

| Command           | Description                                                        |
|-------------------|--------------------------------------------------------------------|
| `npm run dev`        | Dev server with hot reload at `http://localhost:5173`               |
| `npm run build`      | Type-check (`tsc -b`), then build the production bundle to `dist/` |
| `npm run preview`    | Serve the production build locally                                  |
| `npm run smoke`      | Build, then serve and verify nested-route deep links load           |
| `npm run lint`       | Lint the source (oxlint)                                            |
| `npm test`           | Run the test suite (Vitest + Testing Library, jsdom)                |
| `npm run generate:api` | Regenerate the typed API client from `docs/openapi.yaml`          |

## Deep-link smoke check

`npm run smoke` builds the bundle, serves it with `vite preview`, and requests
several routes directly — the way a browser does on first load or refresh —
including the nested routes `/repairs/1`, `/repairs/new`,
`/repairs/1/work-log/2`, and `/magazzino/bombole/1`. For each route it resolves
the entry document's module script and stylesheet against that route's URL and
asserts the server returns them as JavaScript / CSS. This guards the asset base
(`base` in `vite.config.ts`): a relative base makes nested routes request
`/repairs/assets/...`, which the SPA fallback answers with `index.html`, so the
app never mounts and the page is blank.

## Dev proxy

The Vite dev server proxies `/api` and `/healthz` to
`http://127.0.0.1:5000`, so the app talks to the backend same-origin
(no CORS configuration needed). Start the backend with `make run` before
relying on data from the app.

## Layout

```
src/
  App.tsx             # ThemeProvider + CssBaseline + BrowserRouter + route map
  theme.ts            # MUI theme — the single place to rebrand
  components/
    AppShell.tsx      # App bar (home), breadcrumbs, bottom nav, routed content
    SearchModal.tsx   # Cached, client-filtered reference picker (customers/vehicles/parts)
  pages/
    HomePage.tsx        # Active repairs (landing at /)
    RepairsListPage.tsx # All repairs, filters, delete, Excel export
    RepairPage.tsx      # New/edit repair, parts table, work-log table, archive
    WorkLogPage.tsx     # Work-log entry editor (times, operator, gas recharge)
    MagazzinoPage.tsx   # Placeholder
    AnagraficaPage.tsx  # Placeholder
    NotFoundPage.tsx    # Catch-all
  api/
    client.ts         # Shared /api/v1 client: generated types + ApiError envelope decoding
    repairs.ts        # Repairs/work-log data access + export URL
    reference.ts      # Customers and vehicles
    equipment.ts      # Service parts and gas cylinders
    generated/        # Generated from docs/openapi.yaml (committed — see "API client")
  hooks/useApi.ts     # Minimal loading/error hook over the shared client
  lib/                # format.ts (hours/dates) and download.ts
  test/setup.ts       # Vitest setup: browser-like relative-URL Request shim for jsdom
```

## API client (generated)

`src/api/generated/schema.d.ts` is generated from
[`docs/openapi.yaml`](../docs/openapi.yaml) and is **committed** to the repo
(a type declaration only, no runtime cost), so `npm run build`, `lint`, and
`test` all work from a fresh checkout with no generation step.

If you change `docs/openapi.yaml`, regenerate the client and commit the diff:

```bash
npm run generate:api
```

The runtime is `openapi-fetch` (a thin typed wrapper over `fetch`); the
`generate:api` tool is `openapi-typescript`.

The repairs screens (landing, list with search/export, repair detail with parts
and work log, work-log editor) are implemented. The Magazzino, Anagrafica, and
Ricambi screens remain planned as follow-up changes on top of this shell.
