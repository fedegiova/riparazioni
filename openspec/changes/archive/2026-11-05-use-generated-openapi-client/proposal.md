# Proposal

## Why

The frontend's data access is a hand-written, untyped helper
(`src/api/client.ts` → `request<T>(method, path, body?)`): every endpoint a
future screen calls needs a hand-maintained type and a hand-rolled URL string,
and nothing in the frontend is checked against `docs/openapi.yaml`, the
machine-readable contract of the `/api/v1` API. The scaffold change that
introduced this client explicitly deferred codegen ("revisit if the endpoint
count grows"); the frontend is about to grow feature screens, so the typed
API surface should now derive from the spec instead of being re-typed by hand
a second time.

## What Changes

- Add OpenAPI code generation to the frontend: an npm script
  (`generate:api`) that derives the API types from `docs/openapi.yaml` into
  the frontend source tree, plus a small generated-client runtime
  (fetch-based) that provides typed per-endpoint calls for every operation in
  the spec (paths, query params, request bodies, response shapes).
- **BREAKING (frontend-internal)**: replace the hand-written generic
  `request<T>(method, path, body?)` helper with the generated, fully typed
  client. Nothing in the app currently calls `request` (only its own tests),
  so no screen behavior changes; future screens call generated operations.
- Keep the established client contract on top of the generated client:
  same-origin relative URLs under `/api/v1` (no hard-coded origin) and
  rejection with `ApiError` carrying the backend
  `{"error": "message"}` envelope message on 4xx/5xx (with the same
  non-envelope fallback).
- Update the frontend test suite to exercise the generated client
  (envelope decoding, typed 2xx decoding, a type-level check that generated
  types track the spec) and update `frontend/README.md` with the new script.
- Generated artifacts are committed to the repo; regenerating after an
  `openapi.yaml` change is a documented developer step.

Out of scope: any feature screens (repairs, equipment, pictures — planned as
follow-up changes), backend changes, changes to `docs/openapi.yaml` itself,
CI changes (no frontend CI job exists yet), and production serving of the
bundle.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `frontend-app`: the "API client against the /api/v1 backend" requirement
  changes — the shared client is now generated from the OpenAPI document
  (types and per-endpoint call signatures derive from
  `docs/openapi.yaml`), replacing the hand-written untyped helper, while
  preserving the relative-URL and error-envelope behaviors; a new requirement
  adds the code-generation workflow (npm script + committed generated
  output). The "Type-checked development and build workflow" requirement
  changes to include the `generate:api` script in the documented npm script
  set.

## Impact

- **Modified code**: `frontend/src/api/` (hand-written `request` helper
  replaced by generated client + thin error-envelope wrapper; tests updated),
  `frontend/package.json` (two new dev/runtime dependencies for the codegen
  toolchain), `frontend/README.md` (scripts + layout).
- **New files**: generated API client output under `frontend/src/api/`
  (committed), plus the frontend-side codegen configuration.
- **No changes** to `app/`, `migrations/`, `tests/`, `docs/openapi.yaml`, the
  Flask API, or the database. The backend is consumed as-is.
- **Dependencies**: two new npm packages on the frontend only
  (a type generator and a fetch-based typed client runtime); no Python or
  runtime-deployment impact.
