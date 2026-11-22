# Proposal

## Why

Opening or refreshing a nested route (`/repairs/1`, `/repairs/new`,
`/repairs/:id/work-log/:entryId`, `/magazzino/bombole/:id`) directly renders a
blank page. The production bundle is built with a relative asset base
(`base: './'`), so `dist/index.html` asks for `./assets/index-*.js`; on a route
with two or more segments the browser resolves that against the route
(`/repairs/assets/...`), the module is not served as JavaScript, and the app
never mounts. Single-segment routes (`/settings`, `/repairs`, `/magazzino`,
`/anagrafica`) happen to resolve back to `/assets/...` and work.

## What Changes

- Build the production bundle with a root-absolute asset base (`base: '/'`) so
  the entry document always loads its script and stylesheet from
  `/assets/...`, independent of the current route.
- Add a smoke check that builds the bundle, serves it, requests a nested URL
  directly, and asserts the app entry document and its resolved module load as
  JavaScript (the failure that leaves the page blank).
- Add a fast unit test that pins the build base to the application root.
- Document the smoke check in `frontend/README.md`.

No runtime behavior changes on single-segment routes, and no backend or API
changes.

## Capabilities

### New Capabilities
<!-- None: this is a defect fix, not a new capability. -->

### Modified Capabilities
- `frontend-app`: direct navigation to and refreshing of a nested route must
  load the application shell, and the built entry document must reference its
  assets from the application root.

## Impact

- Frontend build config: `frontend/vite.config.ts` (`base`).
- Frontend tests/tooling: a new smoke script under `frontend/scripts/` plus an
  npm `smoke` script and a `frontend-app` config unit test.
- Docs: `frontend/README.md`.
- No changes to the Flask backend, `docs/openapi.yaml`, the database, or the
  application routes. Production serving of the built bundle (an Nginx/static
  host with history fallback) remains a separate, deferred concern; `vite
  preview` already rewrites unknown paths to `index.html`.
