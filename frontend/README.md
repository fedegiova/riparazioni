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
| `npm run lint`       | Lint the source (oxlint)                                            |
| `npm test`           | Run the test suite (Vitest + Testing Library, jsdom)                |
| `npm run generate:api` | Regenerate the typed API client from `docs/openapi.yaml`          |

## Dev proxy

The Vite dev server proxies `/api` and `/healthz` to
`http://127.0.0.1:5000`, so the app talks to the backend same-origin
(no CORS configuration needed). Start the backend with `make run` before
relying on data from the app.

## Layout

```
src/
  App.tsx             # ThemeProvider + CssBaseline + BrowserRouter + shell (AppBar)
  theme.ts            # MUI theme — the single place to rebrand
  pages/              # Routed pages (HomePage at /, NotFoundPage on catch-all)
  api/client.ts       # Shared /api/v1 client: generated types + ApiError envelope decoding
  api/generated/      # Generated from docs/openapi.yaml (committed — see "API client")
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

Feature screens (repairs, equipment, pictures) are planned as follow-up
changes on top of this shell.
