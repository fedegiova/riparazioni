# frontend-app Specification

## Purpose

The `frontend-app` capability is the React web application for the repair
management system: it defines the application shell and Material Design
theming, how the frontend talks to the backend API, and the development and
build workflow for the frontend codebase.

## Requirements

### Requirement: Application shell with Material theme

The web application SHALL present a Material Design app shell: a top app bar
with a control that returns to the landing route and a settings control that
opens the settings page, a breadcrumb bar, a content area, and a bottom
navigation with the destinations Repairs List, Magazzino, and Anagrafica,
rendered with a single application theme (consistent palette, typography, and
component styling) on every route. The shell SHALL host the active-repairs
landing at `/`, the settings page at `/settings`, and an unhandled route SHALL
render a not-found placeholder instead of crashing.

#### Scenario: Home route renders inside the shell

- **WHEN** a user opens the application root URL
- **THEN** the app shell (app bar, breadcrumb bar, content area, bottom navigation) is visible and the content area shows the active-repairs landing page

#### Scenario: Home control returns to the landing

- **WHEN** a user activates the app bar's home control from another page
- **THEN** the application navigates back to the landing route

#### Scenario: Settings control opens the settings page

- **WHEN** a user activates the app bar's settings control
- **THEN** the application navigates to the settings route and the content area shows the settings page

#### Scenario: Settings route renders inside the shell

- **WHEN** a user opens the settings route directly
- **THEN** the app shell is visible and the content area shows the settings page

#### Scenario: Bottom navigation switches sections

- **WHEN** a user selects a bottom-navigation destination
- **THEN** the application shows that section's page and marks the destination as selected

#### Scenario: Unhandled route shows not-found placeholder

- **WHEN** a user navigates to a URL that matches no defined route
- **THEN** the shell remains visible and the content area shows a not-found placeholder page, without an unhandled error

### Requirement: API client against the /api/v1 backend

The frontend SHALL provide a shared client module that all data access uses,
whose per-endpoint call signatures and request/response types are generated
from `docs/openapi.yaml` (no hand-maintained duplicates of the API shape).
The client SHALL use same-origin relative URLs under `/api/v1` (no hard-coded
backend origin), decode 2xx responses as JSON, and reject the backend error
envelope `{"error": "message"}` (4xx/5xx) with its message so the UI can
present errors.

#### Scenario: Successful request returns decoded data

- **WHEN** the client requests an `/api/v1` resource and the backend returns a 2xx response
- **THEN** the caller receives the parsed JSON body, typed to the response shape declared in the OpenAPI document

#### Scenario: Request shape is checked against the OpenAPI document

- **WHEN** application code calls an endpoint with a path, method, query parameter, or request body that does not match the OpenAPI document
- **THEN** the frontend type check fails to compile, reporting the mismatch

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
the source), `test` (run the test suite), and `generate:api` (regenerate the
API client from `docs/openapi.yaml`). The codebase SHALL be TypeScript with
strict type checking, and `build` SHALL fail when type errors exist.

#### Scenario: Dev server starts and hot-reloads

- **WHEN** a developer runs `npm run dev` and edits a source file
- **THEN** the dev server serves the updated application without a full page reload

#### Scenario: Production build succeeds and is type-safe

- **WHEN** a developer runs `npm run build` on a codebase without type errors
- **THEN** an optimized static bundle is produced; and when a type error is introduced, the same command fails with that type error reported

#### Scenario: Lint and test scripts run

- **WHEN** a developer runs `npm run lint` and `npm test`
- **THEN** static analysis runs over the frontend source and the frontend test suite executes, with failures reported as non-zero exits

#### Scenario: generate:api script rebuilds the API client

- **WHEN** a developer runs `npm run generate:api` after changing `docs/openapi.yaml`
- **THEN** the generated API client (types and per-endpoint call signatures) is rewritten to match the updated document

### Requirement: API client code generation workflow

The frontend SHALL provide an npm script that regenerates the API client —
its types and per-endpoint call signatures — from the OpenAPI document at
`docs/openapi.yaml`, and the generated output SHALL be committed to the
repository. Linting, type-checking, testing, and building SHALL work from a
fresh checkout without a prior generation step, and regenerating after an
OpenAPI document change SHALL update the client to match the document.

#### Scenario: Regeneration updates the client to match the document

- **WHEN** the OpenAPI document is changed (for example a new endpoint or a new response field) and the frontend regeneration script is run
- **THEN** the generated client exposes the changed endpoint or field in its types and per-endpoint call signatures

#### Scenario: Fresh checkout works without generation

- **WHEN** a developer runs the frontend's lint, type-check, test, or build scripts after a fresh checkout, without running the regeneration script
- **THEN** the scripts succeed against the committed generated client

### Requirement: Deep-linkable application routes

The application SHALL load the routed page when a user opens or refreshes any
application URL directly, including routes with two or more path segments. The
served entry document SHALL reference the entry script and stylesheet by a
location that does not depend on the current route, so the module executes and
the app mounts instead of leaving the page blank.

#### Scenario: Nested route opened directly renders inside the shell

- **WHEN** a user opens a nested route such as `/repairs/1`, `/repairs/new`, `/repairs/1/work-log/2`, or `/magazzino/bombole/1` directly
- **THEN** the app shell is visible and the content area shows that route's page, not a blank page

#### Scenario: Refreshing a nested route reloads the routed page

- **WHEN** a user is on a nested route and reloads the page
- **THEN** the app shell and the routed page are shown again

#### Scenario: Unknown deep link shows the not-found placeholder

- **WHEN** a user opens a URL that matches no defined route, including a nested one
- **THEN** the shell remains visible and the content area shows the not-found placeholder, without an unhandled error

#### Scenario: Built entry document loads its module regardless of route

- **WHEN** the production bundle's entry document is served for a nested route and the browser requests the script it references
- **THEN** the script is served as JavaScript from the application root, so the module executes
