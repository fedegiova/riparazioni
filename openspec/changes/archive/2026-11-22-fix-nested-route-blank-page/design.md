# Design

## Context

See proposal.md — Why. The frontend is a history-mode SPA (`BrowserRouter`,
route table in `frontend/src/App.tsx`) served as a static bundle from
`frontend/dist`. `frontend/vite.config.ts` currently sets `base: './'` so the
build can be served "from `/` or any subpath" (archived decision 6 of
`add-vite-react-frontend`).

The observed mechanism is more precise than a 404: with `base: './'`,
`dist/index.html` references `./assets/index-*.js`. Requested at
`/repairs/1`, the browser resolves that to `/repairs/assets/index-*.js`. The
`vite preview` SPA fallback serves `index.html` there with
`Content-Type: text/html`, so the module request "succeeds" with 200 but is not
JavaScript; the browser refuses to execute it and `#root` stays empty. Routes
with a single segment resolve `./assets/...` back to `/assets/...` and work.

## Goals / Non-Goals

**Goals:**

- Any application URL — including multi-segment routes — loads the app shell on
  direct navigation and refresh.
- A committed smoke check that fails when the entry document's assets are
  requested from a route-dependent path.

**Non-Goals:**

- Production serving of `frontend/dist` (Nginx/static host, history fallback).
  Deferred by the initial frontend change and not wired up today; the reported
  environment is `vite preview`, whose fallback already rewrites unknown paths
  to `index.html`.
- Subpath deployment support. The app's routes are root-relative and
  `BrowserRouter` has no `basename`, so serving under a prefix was never
  functional; `base: '/'` removes a flexibility that did not work.
- Changing routes, the SPA fallback, or any backend/API behavior.

## Decisions

**Use a root-absolute asset base (`base: '/'`).**
The entry document then references `/assets/index-*.js` and
`/assets/index-*.css`, which resolve identically on every route, so the module
loads and React mounts. Chosen over the alternatives: keeping `base: './'` and
adding `<base href="/">` is equivalent for assets but adds a second place that
can drift; calculating a base at deploy time is unnecessary because the app has
a single root deployment.

**Verify with a build-level smoke check, not a jsdom test.**
The defect lives in the built `index.html` asset URLs and only manifests when a
server serves the bundle; a jsdom render at `/repairs/1` succeeds with either
base because jsdom does not fetch assets. A small Node script builds, starts
`vite preview`, requests nested URLs, extracts the module `src`, resolves it
against the nested URL, and asserts it is served as JavaScript. The script is a
`npm run smoke` target and is documented, not added to CI (CI does not run the
frontend today).

**Pin the config in the unit suite as well.**
A fast Vitest case asserts the resolved Vite `base` is the application root, so
a regression is caught by `npm test` without a build.

## Risks / Trade-offs

- [A future move to a subpath deployment would break with `base: '/'`] → Such a
  deployment also needs a router `basename` and a server rewrite; it is a
  deliberate, documented non-goal, not a silent regression.
- [The smoke script starts a server and builds, so it is slower than a unit
  test] → It is opt-in (`npm run smoke`), while the unit suite guards the config
  cheaply.
- [History fallback is still required in any real static deployment] → Noted in
  the existing deployment docs; `vite preview` provides it for the smoke check,
  and the relative base was the blocking defect.

## Migration Plan

Frontend build-config change plus tests/docs; no schema or data migration. A
release rebuilds `frontend/dist` and deploys as usual; rollback reverts the
commit.

## Open Questions

None.
