# Spec Delta

## Purpose

The `frontend-app` capability is the React web application for the repair
management system: it defines the application shell and Material Design
theming, how the frontend talks to the backend API, and the development and
build workflow for the frontend codebase.

## ADDED Requirements

### Requirement: Application shell with Material theme

The web application SHALL present a Material Design app shell: a persistent
top navigation area and a content area, rendered with a single application
theme (consistent palette, typography, and component styling) on every
route. The shell SHALL host a home route at `/` with placeholder content, and
an unhandled route SHALL render a not-found placeholder instead of crashing.

#### Scenario: Home route renders inside the shell

- **WHEN** a user opens the application root URL
- **THEN** the app shell (top navigation + content area) is visible and the content area shows the placeholder home page with application branding

#### Scenario: Unhandled route shows not-found placeholder

- **WHEN** a user navigates to a URL that matches no defined route
- **THEN** the shell remains visible and the content area shows a not-found placeholder page, without an unhandled error

### Requirement: API client against the /api/v1 backend

The frontend SHALL provide a shared client module that all data access uses,
calling the backend through same-origin relative URLs under `/api/v1` (no
hard-coded backend origin). Successful responses SHALL be decoded as JSON and
returned to the caller; responses with the backend error envelope
`{"error": "message"}` (4xx/5xx) SHALL be rejected with the message, and the
client SHALL surface the request/response structure needed for later screens
to display these errors.

#### Scenario: Successful request returns decoded data

- **WHEN** the client requests an `/api/v1` resource and the backend returns a 2xx response
- **THEN** the caller receives the parsed JSON body, typed to the response shape

#### Scenario: Backend error is rejected with its message

- **WHEN** the backend responds to a client request with a 4xx or 5xx status and the `{"error": "message"}` envelope
- **THEN** the client rejects the request carrying that error message so the UI can present it

### Requirement: Development proxy to the local backend

In development, the frontend dev server SHALL forward requests for `/api`
and `/healthz` to the local Flask backend at `127.0.0.1:5000`, so the
application runs same-origin against a local backend without CORS
configuration.

#### Scenario: Dev server proxies API calls

- **WHEN** the app is running via the dev server and makes a request to `/api/v1/...`
- **THEN** the request is served by the local Flask backend at `127.0.0.1:5000` and the response returns to the app unchanged

#### Scenario: Dev server health check is proxied

- **WHEN** the dev server receives a request for `/healthz`
- **THEN** the request is proxied to the local Flask backend and its response (including a 503 from `/healthz/db` when the database is unreachable) is returned to the caller

### Requirement: Type-checked development and build workflow

The frontend SHALL provide the npm scripts `dev` (start the dev server with
hot reload), `build` (produce an optimized, static production bundle),
`preview` (serve the production bundle locally), `lint` (static analysis of
the source), and `test` (run the test suite). The codebase SHALL be
TypeScript with strict type checking, and `build` SHALL fail when type
errors exist.

#### Scenario: Dev server starts and hot-reloads

- **WHEN** a developer runs `npm run dev` and edits a source file
- **THEN** the dev server serves the updated application without a full page reload

#### Scenario: Production build succeeds and is type-safe

- **WHEN** a developer runs `npm run build` on a codebase without type errors
- **THEN** an optimized static bundle is produced; and when a type error is introduced, the same command fails with that type error reported

#### Scenario: Lint and test scripts run

- **WHEN** a developer runs `npm run lint` and `npm test`
- **THEN** static analysis runs over the frontend source and the frontend test suite executes, with failures reported as non-zero exits
