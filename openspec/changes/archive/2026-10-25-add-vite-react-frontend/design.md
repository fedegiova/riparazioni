# Design

## Context

See proposal.md for motivation. The backend is a Flask app (dev:
`flask run` on `127.0.0.1:5000`, prod: gunicorn behind Nginx) exposing a
JSON API under `/api/v1` with error envelope `{"error": "message"}` (400/404/
405/409), plus `/healthz` and `/healthz/db` (503 when DB unreachable). The
machine-readable contract is `docs/openapi.yaml`. There is currently no
frontend code: `app/static` and `app/templates` are empty placeholders. The
repo is a single git repository on Node 22 / npm 12.

Constraints:

- No backend changes: the frontend must consume the existing API as-is,
  including its error envelope and read-only reference-data endpoints.
- Monorepo: the frontend lives in `frontend/` inside this repo, coexisting
  with the Python backend and its Makefile workflow.

## Goals / Non-Goals

**Goals:**

- A working Vite + React + TypeScript app under `frontend/` with a Material
  Design app shell (theme, top navigation, routed home + not-found pages).
- A shared, typed API client module over relative `/api/v1` URLs that later
  feature-screen changes can build on without re-plumbing.
- A standard, reproducible dev/build/lint/test workflow from npm scripts.

**Non-Goals:**

- No feature screens (repairs, equipment, pictures, reference data) — those
  are follow-up changes on top of this shell.
- No authentication/authorization (the backend has none today).
- No production serving of the built bundle (no Nginx/Flask static config
  changes in this change; that is decided when the first screens exist).
- No backend changes, no OpenAPI client codegen, no state-management layer
  (Redux etc.) — data fetching needs appear with the first screens.

## Decisions

### 1. Scaffold from the official Vite `react-ts` template

`npm create vite@latest frontend -- --template react-ts` inside the repo
root, then install dependencies and add the extras below. The template gives
us the current, mutually compatible set of tooling (Vite 7.x, React 19.x,
TypeScript strict config split into `tsconfig.app.json` /
`tsconfig.node.json`, ESLint 9 flat config with react-hooks/react-refresh
plugins) and its own `frontend/.gitignore` covering `node_modules`, `dist`,
and editor/OS noise.

*Alternatives considered:* hand-rolling the config (more control, more
drift risk, no reason not to start from the maintained template); a separate
repo (rejected in planning — one deployment pipeline and shared history are
preferred).

### 2. MUI (Material UI) v7 with Emotion

Install `@mui/material`, `@emotion/react`, `@emotion/styled`, and
`@mui/icons-material` (current major as of implementation). MUI is the
de-facto standard React implementation of Material Design and directly
answers the request for "material design components". Theme is defined in
`src/theme.ts` via `createTheme` — MUI default palette/typography for now
(no brand assets exist in the repo; the theme module is the single place to
change it later) — wrapped with `ThemeProvider` + `CssBaseline` at the app
root.

*Alternatives considered:* Vuetify and react-md (both viable, but MUI has the
largest ecosystem and the clearest "Material Design components" match for
this request).

### 3. App shell with React Router v7

`react-router-dom` (v7) with `BrowserRouter` + `<Routes>`: `/` →
`HomePage` (placeholder content with app branding), catch-all `*` →
`NotFoundPage`. The shell layout (MUI `AppBar` with app title + `Box`
content area) wraps the routed outlet so navigation chrome persists. This
sets the structure that later screen changes extend with real routes
(e.g. `/repairs`, `/equipment`).

*Alternatives considered:* no router for now (rejected — every later screen
change would pay for the routing retrofit); nested route configs with
`createBrowserRouter` (deferrable — `BrowserRouter` + declarative `<Routes>`
is enough for a shell and reads simpler).

### 4. API client: plain `fetch`, no generated types, no HTTP library

A small module `src/api/client.ts` exporting a typed helper
`request<T>(method, path, body?)` that:

- prefixes `/api/v1` and sends `Content-Type: application/json` (the picture
  upload endpoint's multipart path will be handled by a dedicated call when
  the pictures screen lands — not pre-built now);
- parses JSON on 2xx;
- on non-2xx, reads the `{"error": "message"}` envelope and rejects with an
  `ApiError extends Error` carrying `status` and the message (also tolerates
  non-envelope bodies by falling back to a generic message with the status).

No axios (fetch covers all present/future needs; one fewer dependency), no
OpenAPI codegen (the API surface is small and stable; generated types would
churn with every endpoint change and the client stays a few dozen lines).
Later screen changes add per-endpoint functions in `src/api/*.ts` on top of
this helper.

*Alternatives considered:* codegen from `docs/openapi.yaml` (rejected for
the scaffold; revisit if the endpoint count grows); per-call `fetch` in each
screen (rejected — the envelope decoding would be copy-pasted everywhere).

### 5. Dev proxy: `/api` and `/healthz` → `127.0.0.1:5000`

`vite.config.ts` sets `server.proxy` for `/api` and `/healthz` to target
`http://127.0.0.1:5000` (the port `make run` / `flask run` binds). This
keeps the app same-origin in development: relative API URLs, no CORS, and
the client code is identical in dev and in a same-origin production
deployment.

*Alternatives considered:* absolute backend URL + CORS on Flask (requires a
backend change and a CORS misconfiguration class of problems; rejected —
the no-backend-change constraint is also stronger); making the proxy target
env-configurable now (YAGNI; the Flask dev port is fixed in the README).

### 6. Build output stays static and path-flexible

`npm run build` outputs a static bundle to `frontend/dist` with
`base: './'` so the bundle can later be served by Nginx from `/` or any
subpath without rebuilds. SPA history-mode fallback rewrites are **not**
part of this change (production serving is out of scope); the decision
recorded here is simply that the bundle will not assume an absolute asset
origin.

### 7. Testing: Vitest + Testing Library, on top of the template baseline

The Vite react-ts template ships a Vitest baseline; extend it with
`@testing-library/react` + `jsdom` and add two concrete tests pinning the
spec:

- API client: a mocked 4xx response with the `{"error": ...}` envelope
  rejects with `ApiError` carrying that message; a 2xx response resolves to
  the parsed body.
- Shell: the app renders the themed shell with the home page at `/` and the
  not-found placeholder on an unmatched route.

### 8. Lint and type checking

Keep the template's ESLint flat config (typescript-eslint, react-hooks,
react-refresh); `npm run lint` runs `eslint .`. Type checking is enforced by
the `build` script chain (`tsc -b && vite build` from the template), so a
type error fails the build — matching the spec's type-safe-build requirement.
No new lint rules in this change.

## Risks / Trade-offs

- [Proxy target down] → if the Flask dev server isn't running, proxied API
  calls fail (500/504 from the dev server). Mitigation: document in
  `frontend/README.md` that `make run` (root Makefile) must be started first;
  the not-found/home shell renders fine without the backend.
- [MUI major churn] → MUI v7 vs v5/v6 differences (e.g. slot APIs) can make
  old examples mislead implementers. Mitigation: pin the current major in
  `package.json` and reference the installed docs, not generic blog posts.
- [Placeholder-only scope feels thin] → this change delivers no screens.
  Mitigation: the API client + shell are intentionally the reusable base;
  each follow-up screen change is small and mechanical on top of them.
- [Nested frontend/.gitignore vs root] → git handles nested .gitignore files
  fine; nothing is lost, and the root `.gitignore` stays Python-only.

## Migration Plan

Pure addition: nothing existing is modified. Rollback is deleting
`frontend/` (no backend, DB, or deployment impact). No data migration.

## Open Questions

None — production serving of the built bundle is deliberately deferred to a
separate change (explicit non-goal) and can be answered then without
touching this change's artifacts.
