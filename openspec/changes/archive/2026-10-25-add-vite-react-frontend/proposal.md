# Proposal

## Why

The repair-management backend (Flask + MSSQL, `/api/v1` API with an OpenAPI
spec at `docs/openapi.yaml`) is complete, but there is no user interface: the
only consumers are curl-level clients. Operators need a web app to manage
repairs, equipment, and pictures. This change lays the frontend foundation —
a Vite + React + TypeScript application with Material Design components — so
feature screens can be built incrementally in follow-up changes.

## What Changes

- Add a new frontend application in the `frontend/` subdirectory of this
  repo: Vite + React + TypeScript (Vite's `react-ts` template).
- Use MUI (Material UI) as the component library, with an app-wide Material
  theme (MUI v5+ createTheme, IBM Plex Sans default font).
- Add an app shell: React Router with a top-level layout (MUI
  `AppBar`/`Drawer` or equivalent) and a placeholder home page — no feature
  screens in this change.
- Add a thin API client module that calls the existing `/api/v1` endpoints
  via relative URLs and decodes the standard `{"error": "message"}` error
  envelope; usable by later screen-level changes without re-plumbing.
- Wire the dev workflow: Vite dev server proxies `/api` (and `/healthz`) to
  the local Flask app at `127.0.0.1:5000`; `npm run dev` / `build` /
  `preview` / `lint` / `test` scripts; ESLint with the TS + React presets.
- Add `frontend/.gitignore` (node_modules, dist, local build output) via the
  Vite scaffold.

Out of scope: any feature screens (repairs, equipment, pictures), backend
changes, authentication, and serving the built bundle from the Flask/Nginx
production deployment (a separate change once screens exist).

## Capabilities

### New Capabilities

- `frontend-app`: the React web application for repair management — toolchain
  (Vite/TypeScript), Material UI theming, app shell and routing, API client
  for `/api/v1`, and the frontend development/build workflow.

### Modified Capabilities

(none — no backend requirements change)

## Impact

- **New code**: `frontend/` directory (package.json, tsconfig, vite config,
  ESLint config, its own `.gitignore`, and `src/` with app shell, theme, and
  API client).
- **No changes** to `app/`, `migrations/`, `tests/`, the `/api/v1` API, or
  the database. The backend is consumed as-is.
- **Tooling**: developer machines need Node 22+ / npm (already present in the
  environment where this is being developed); no runtime dependency added to
  the Python app.
