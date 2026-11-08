# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
