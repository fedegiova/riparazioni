# Tasks

## 1. Production asset base

- [x] 1.1 In `frontend/vite.config.ts`, replace `base: './'` with a root-absolute base (`base: '/'`) and a comment explaining that nested routes break with a relative base; verify `npm run build` produces a `frontend/dist/index.html` whose script and stylesheet URLs start with `/assets/` and whose favicon URL starts with `/`
- [x] 1.2 Add a fast unit test that pins the resolved Vite `base` to the application root (for example `frontend/src/vite-config.test.ts`), and verify `npm test` passes

## 2. Deep-link smoke check

- [x] 2.1 Add `frontend/scripts/smoke-deep-link.mjs` and an npm `smoke` script (`npm run build && node scripts/smoke-deep-link.mjs`): it serves the built bundle via `vite preview`, requests the nested routes `/repairs/1`, `/repairs/new`, `/repairs/1/work-log/2`, and `/magazzino/bombole/1` directly, asserts each returns the entry document, extracts the module script `src`, resolves it against the nested URL, and asserts it is served as JavaScript; verify `npm run smoke` exits 0
- [x] 2.2 Document `npm run smoke` in `frontend/README.md` (what it checks and that it runs a production build first) and verify the documented command runs as written

## 3. Integration verification

- [x] 3.1 Run `npm test`, `npm run lint`, `npm run build`, and `npm run smoke` in `frontend/` and confirm all exit 0; confirm no files under `app/`, `migrations/`, `tests/`, or `docs/` changed
