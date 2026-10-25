# Tasks

## 1. Scaffold and dependencies

- [x] 1.1 Run `npm create vite@latest frontend -- --template react-ts` at the repo root and verify `frontend/` contains `package.json`, `tsconfig.app.json`, `tsconfig.node.json`, `vite.config.ts`, `eslint.config.js`, `index.html`, `src/main.tsx`, and its own `.gitignore`
- [x] 1.2 Run `npm install` inside `frontend/` and verify the template baseline passes: `npm run build` exits 0
- [x] 1.3 Remove template boilerplate (`src/App.css`, `src/assets/`, the default counter in `src/App.tsx` and its test file) and verify `npm run build` still exits 0
- [x] 1.4 Add runtime dependencies `@mui/material`, `@emotion/react`, `@emotion/styled`, `@mui/icons-material`, `react-router-dom` and verify they resolve: `npm ls @mui/material react-router-dom` shows the installed versions

## 2. Theme and app shell

- [x] 2.1 Create `frontend/src/theme.ts` defining the MUI theme with `createTheme` (default palette/typography, single place to rebrand later) and verify `npm run build` type-checks it
- [x] 2.2 Restructure `src/App.tsx` into the shell: `ThemeProvider` (theme from `src/theme.ts`) + `CssBaseline` + `BrowserRouter` + a persistent `AppBar` with app title wrapping the routed content area, and verify `npm run build` exits 0
- [x] 2.3 Add `src/pages/HomePage.tsx` (placeholder with app branding at `/`) and `src/pages/NotFoundPage.tsx` (catch-all `*` route), then verify in dev: `npm run dev`, opening `/` shows the home placeholder inside the shell and opening an unknown URL shows the not-found placeholder with the shell still visible
- [x] 2.4 Add Vitest + `@testing-library/react` + `jsdom` to dev dependencies, a shell test asserting the home page renders at `/` and the not-found placeholder renders on an unmatched route, and verify `npm test` passes

## 3. API client

- [x] 3.1 Create `frontend/src/api/client.ts` exporting `ApiError` and a typed `request<T>(method, path, body?)` helper: `/api/v1` prefixing, JSON `Content-Type`, 2xx parsed to `T`, non-2xx decoding the `{"error": "message"}` envelope into `ApiError` (with `status`) and falling back to a generic message with the status when the envelope is absent, and verify `npm run build` type-checks it
- [x] 3.2 Add API client tests mocking `fetch`: a 2xx response resolves to the parsed body, a 4xx response with the error envelope rejects with an `ApiError` carrying that message, and a 4xx response without the envelope rejects with a fallback message including the status, and verify `npm test` passes

## 4. Dev proxy, build config, and docs

- [x] 4.1 Add `server.proxy` entries for `/api` and `/healthz` → `http://127.0.0.1:5000` in `vite.config.ts` and verify with both servers running (`make run` at the root, `npm run dev` in `frontend/`): `curl http://127.0.0.1:5173/healthz` returns the Flask liveness response and `curl http://127.0.0.1:5173/api/v1/vehicles` returns backend JSON
- [x] 4.2 Set `base: './'` in the Vite build config and verify `npm run build` produces `frontend/dist/` whose `index.html` references assets with relative paths
- [x] 4.3 Write `frontend/README.md` covering prerequisites (Node 22+, backend running via `make run`), the npm scripts (`dev`, `build`, `preview`, `lint`, `test`), and the dev proxy behavior, and verify the documented commands run as written

## 5. Integration checks

- [x] 5.1 Run the full frontend workflow and verify all green: `npm run lint` exits 0, `npm run build` exits 0, `npm test` passes
- [x] 5.2 Verify `git status` shows only intended additions under `frontend/` and `openspec/changes/add-vite-react-frontend/` (scaffold's `.gitignore` keeps `node_modules/` and `dist/` out) and that no files under `app/`, `migrations/`, or `tests/` were modified
