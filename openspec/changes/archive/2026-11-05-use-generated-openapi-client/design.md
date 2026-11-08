# Design

## Context

See proposal.md for motivation. Current state (all under `frontend/`):

- Vite 8 + React 19 + TypeScript 6 (strict, `tsc -b` in the `build` chain) +
  MUI 9; shell-only app (`App.tsx` routes `/` and `*`).
- The only data-access code is the hand-written
  `src/api/client.ts`: `request<T>(method, path, body?)` over relative
  `/api/v1` URLs, `ApiError(status, message)`, envelope decoding of
  `{"error": "message"}` on 4xx/5xx, `204 → undefined`. Nothing in the app
  calls it yet (only `client.test.ts`); it is the base for future screens.
- The API contract is `docs/openapi.yaml` (OpenAPI 3.0.3): 5 tags
  (`reference-data`, `equipment`, `pictures`, `repairs`, `work-log`), ~20
  paths under `/api/v1`, all with typed `components/schemas`. The picture
  upload is `multipart/form-data`; `GET /api/v1/pictures/{picture_id}/file`
  returns `application/octet-stream`.
- Dev proxy: Vite forwards `/api` and `/healthz` to `127.0.0.1:5000`
  (same-origin, no CORS). `npm run lint` is oxlint (`frontend/.oxlintrc.json`);
  `npm test` is Vitest + Testing Library (jsdom). No frontend job exists in
  `.github/workflows/ci.yml` yet.

The scaffold change's design (archived, decision #4) deliberately deferred
codegen; this change reverses that decision now that the API surface is
final and screens are approaching.

Constraints:

- No backend changes: `docs/openapi.yaml` is consumed as-is and stays the
  source of truth; this change must not edit it.
- Preserve the existing client contract (relative URLs, JSON decoding,
  `ApiError` rejection with the envelope message) so future screens are
  written against the same error semantics.

## Goals / Non-Goals

**Goals:**

- The frontend's typed API surface (request/response types and per-endpoint
  call signatures) is generated from `docs/openapi.yaml`, with a single
  documented npm script to regenerate it.
- The hand-written untyped `request()` is replaced by the generated client,
  keeping the `ApiError` rejection contract.
- Generated output is committed, so lint/type-check/test/build work from a
  fresh checkout; drift between spec and client is visible in diffs.

**Non-Goals:**

- No feature screens (repairs, equipment, pictures) — follow-up changes on
  top of this client.
- No React Query / state-management layer, no HTTP library swap beyond the
  chosen codegen runtime.
- No changes to `docs/openapi.yaml`, the backend, CI, or production serving.
- No auto-regeneration hooks (prebuild/watch) — explicit script run.

## Decisions

### 1. Codegen stack: `openapi-typescript` + `openapi-fetch`

Two small packages:

- `openapi-typescript` (devDependency): at build time only, runs
  `openapi-typescript ../docs/openapi.yaml -o src/api/generated/schema.d.ts`,
  emitting the `paths` and `components` types for the whole document.
- `openapi-fetch` (runtime dependency, a few KB): a thin typed client that
  wraps the global `fetch`, parameterized by the generated `paths` type.
  Calling `api('/api/v1/repairs', { method: 'POST', body })` is checked
  against the document: wrong path, method, query param, or body shape fails
  `tsc`.

*Alternatives considered:*

- `@hey-api/openapi-ts`: generates standalone per-operation functions —
  more literally "generated code" but a larger committed blob and a heavier
  toolchain for a ~20-endpoint spec; openapi-fetch gives the same type
  coverage with less churn.
- `orval`: pairs with React Query; we deliberately have no state-management
  layer yet (scaffold decision), so this is over-scoped.
- Types only (`openapi-typescript` + hand-written fetch): keeps the runtime
  dependency out, but then per-endpoint call sites still hand-write URLs and
  parameter assembly — exactly the drift risk this change removes.

### 2. Generated output: committed under `src/api/generated/`

- `src/api/generated/schema.d.ts` is the generated artifact, committed to
  the repo (not gitignored). Rationale: `npm ci && npm run build` works from
  a fresh checkout with no generation step; type errors in the generated
  types are visible at review; the file is a type declaration (`.d.ts`) with
  no runtime cost.
- `npm run generate:api` regenerates it; after touching
  `docs/openapi.yaml`, a developer re-runs it and commits the diff. Drift
  (spec changed, client not regenerated) surfaces as a red `build`/`test`
  or a stale-diff review signal, not as a runtime surprise.
- Lint exclusion: `.oxlintrc.json` gains an ignore for `src/api/generated/**`
  so generated code is not style-policed (it is rewritten wholesale by the
  generator).
- No `prebuild` hook: forcing generation into `build` would make the build
  depend on the devDependency at a point where a clean checkout plus `npm
  install --omit=dev` (a common CI/production pattern) would lack it.

### 3. Client module shape: thin hand-written wrapper over the generated client

`src/api/client.ts` is rewritten (still the single shared module, same
file path, so future screens import one place). It contains only:

- `export const api = createClient<paths>()` — no `baseUrl`: the document's
  paths already carry the `/api/v1` prefix, so calls remain same-origin
  relative URLs (dev proxy and any same-origin production deployment work
  unchanged).
- The `ApiError` class (unchanged shape: `status`, `message`).
- A global `errorMiddleware` (or equivalent hook, per the installed
  `openapi-fetch` version's API) that decodes the backend envelope and
  throws `ApiError(status, message)` so the standard call
  `await api(...)` keeps today's contract: 2xx resolves, 4xx/5xx rejects
  with the envelope message (fallback `Request failed with status <n>` when
  the body is not an envelope). Non-envelope/empty bodies and 204s resolve
  with `undefined` data, as today.
- Re-exports of the generated types (`paths`, and a convenience alias for
  the `components` schemas) so screens can name types without importing the
  generated file directly.

Multipart/binary: the picture upload (`multipart/form-data`) and the
picture-file download (`application/octet-stream`) are typed by the
generated `paths`; the wrapper must not force JSON semantics on them
(`FormData` bodies pass through; the binary download uses the client's
non-JSON parse option, e.g. `parseAs: 'blob'`, when the pictures screen
lands). A test pins the upload call shape with `fetch` mocked.

*Alternatives considered:* per-screen `api(...)` calls with no wrapper
(rejects — the envelope→`ApiError` decoding would be copy-pasted, breaking
the "shared client module" requirement); keeping `request<T>(method, path,
body)` as a facade over the generated client (rejects — a generic string
facade erases the per-endpoint typing, which is the point of the change).

### 4. `npm run generate:api` script

`package.json` scripts gain `"generate:api": "openapi-typescript ../docs/openapi.yaml -o src/api/generated/schema.d.ts"`
(run from `frontend/`, where the npm script executes; the binary resolves
from local `node_modules/.bin`). No Makefile change in this change (the
root Makefile's `web-*` targets exist only for `dev`; the script is
frontend-documented in `frontend/README.md`, which also gains the new
layout entry for `src/api/generated/`).

### 5. Testing: same scenarios, new mechanism

`client.test.ts` is reworked to drive the generated client with `fetch`
mocked (Vitest, jsdom — no backend):

- 2xx resolves to the parsed body (assert the call hit
  `/api/v1/...` with the right method).
- 4xx/5xx with the `{"error": "..."}` envelope rejects with `ApiError`
  carrying `status` and the message.
- 4xx/5xx with a non-envelope body rejects with the fallback message
  containing the status.
- 204 resolves with `undefined`.
- Type-level: the generated types track the document (e.g. `expectTypeOf`
  on a response field / a compile-time assertion that a body mismatch is a
  type error), plus the multipart upload call shape.

### 6. Dependency placement

- `openapi-fetch` → `dependencies` (bundled into the app).
- `openapi-typescript` → `devDependencies` (build-time generator only).
- Versions are the current majors at implementation time; nothing here
  pins ahead of `npm install`.

## Risks / Trade-offs

- [`errorMiddleware` throw semantics differ by version] → the exact hook
  name/behavior depends on the installed `openapi-fetch` minor. Mitigation:
  the three envelope tests (Decision 5) run against the real client
  configuration, so a contract slip fails the suite, not a screen.
- [Committed generated file goes stale] → a spec change without
  `generate:api` ships stale types. Mitigation: the type-level test ties a
  generated field to the document; README documents the regenerate step;
  the drift shows up as a reviewable diff in the same PR that changes
  `openapi.yaml`.
- [openapi-typescript output style changes between versions] → regenerated
  file can churn (formatting, helper types). Mitigation: pin the devDependency
  in `package-lock.json`; regeneration is idempotent for a given version.
- [Generated code excluded from lint] → the exclusion only covers
  `src/api/generated/**`; all hand-written code stays linted.
- [Multipart/binary edge cases deferred] → the pictures screen (follow-up)
  is where uploads/downloads are exercised for real; this change only pins
  the call shape in tests.

## Migration Plan

Single frontend commit sequence; no backend, DB, or deployment impact:

1. Add dependencies + `generate:api` script; generate
   `src/api/generated/schema.d.ts`; exclude it from lint.
2. Rewrite `src/api/client.ts` as the thin wrapper (Decision 3); update
   `client.test.ts`; update `frontend/README.md`.
3. Verify: `npm run lint`, `npm test`, `npm run build` all green; a red test
   confirms a deliberately wrong call shape fails `tsc`.

Rollback: revert the commit (the old `client.ts` had no production users).
No data migration. If the generated file and the old helper ever coexist in
a partial state, the old export is deleted in the same commit as the new
one — there is no supported intermediate where both are imported.

## Open Questions

None. (CI coverage for the frontend — lint/test/build in
`.github/workflows/ci.yml` — is a separate follow-up; this change assumes
the same local-script verification the project already uses for the
frontend.)
