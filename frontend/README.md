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
| `npm run dev`     | Dev server with hot reload at `http://localhost:5173`               |
| `npm run build`   | Type-check (`tsc -b`), then build the production bundle to `dist/` |
| `npm run preview` | Serve the production build locally                                  |
| `npm run lint`    | Lint the source (oxlint)                                            |
| `npm test`        | Run the test suite (Vitest + Testing Library, jsdom)                |

## Dev proxy

The Vite dev server proxies `/api` and `/healthz` to
`http://127.0.0.1:5000`, so the app talks to the backend same-origin
(no CORS configuration needed). Start the backend with `make run` before
relying on data from the app.

## Layout

```
src/
  App.tsx        # ThemeProvider + CssBaseline + BrowserRouter + shell (AppBar)
  theme.ts       # MUI theme — the single place to rebrand
  pages/         # Routed pages (HomePage at /, NotFoundPage on catch-all)
  api/client.ts  # Shared /api/v1 client: relative URLs, ApiError envelope decoding
```

Feature screens (repairs, equipment, pictures) are planned as follow-up
changes on top of this shell.
