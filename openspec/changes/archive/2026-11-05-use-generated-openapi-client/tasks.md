# Tasks

## 1. Codegen setup

- [x] 1.1 Add `openapi-fetch` to `dependencies` and `openapi-typescript` to `devDependencies` in `frontend/package.json` via `npm install` in `frontend/`; verify `npm install` succeeds and `npx openapi-typescript --help` runs from `frontend/`
- [x] 1.2 Add the npm script `generate:api` (`openapi-typescript ../docs/openapi.yaml -o src/api/generated/schema.d.ts`) to `frontend/package.json` and run it; verify `frontend/src/api/generated/schema.d.ts` exists and exports `paths` containing the `/api/v1/...` keys from `docs/openapi.yaml`
- [x] 1.3 Add an oxlint ignore for `src/api/generated/**` in `frontend/.oxlintrc.json`; verify `npm run lint` passes with the generated file present
- [x] 1.4 Verify regeneration tracks the document: copy `docs/openapi.yaml` to a temp location, add a new response field to the copy, run the generator against the copy into a temp output, confirm the new field appears in the generated types, then delete the temp files and re-run `generate:api` against the real document so the committed file matches it; verify `git status` shows no change to `docs/openapi.yaml` and the committed `schema.d.ts` is unchanged

## 2. Replace the hand-written client

- [x] 2.1 Rewrite `frontend/src/api/client.ts` as the thin wrapper over the generated client — `createClient<paths>()` with no `baseUrl` (same-origin relative URLs), the unchanged `ApiError` class, an error hook that throws `ApiError(status, message)` with the `{"error": "message"}` envelope message (fallback `Request failed with status <n>` for non-envelope bodies) on 4xx/5xx, and re-exports of the generated `paths`/schema types — and delete the hand-written `request<T>()` helper; verify `npx tsc -b` in `frontend/` compiles with no errors
- [x] 2.2 Rework `frontend/src/api/client.test.ts` to drive the generated client with `fetch` mocked: 2xx resolves to the parsed body (assert the call hit the `/api/v1/...` URL with the expected method); 4xx/5xx with the envelope rejects with `ApiError` carrying `status` and the message; 4xx/5xx with a non-envelope body rejects with the fallback message containing the status; 204 resolves with `undefined`; a type-level assertion (`expectTypeOf`) ties a generated response field to the document; the multipart picture-upload call shape is pinned; verify `npm test` passes in `frontend/`
- [x] 2.3 Verify the type-check scenario end to end: temporarily introduce a call in a scratch test file whose request body or path does not match `docs/openapi.yaml`, confirm `npx tsc -b` fails reporting the mismatch, then delete the scratch file and confirm `npx tsc -b` passes again

## 3. Documentation and integration check

- [x] 3.1 Update `frontend/README.md`: add the `generate:api` row to the scripts table, add `src/api/generated/` to the layout section, and note that the generated client is committed and must be regenerated (and committed) after any `docs/openapi.yaml` change; verify the README's script list and layout match `frontend/package.json` and `frontend/src/` on disk
- [x] 3.2 Fresh-checkout verification: in `frontend/`, run `rm -rf node_modules && npm ci`, then without running `generate:api` run `npm run lint`, `npm test`, and `npm run build`; verify all three succeed against the committed generated client
- [x] 3.3 Confirm the spec-level behaviors from the `frontend-app` delta hold together: the app shell still renders (existing `App.test.tsx` passes under `npm test`), no file imports the deleted `request()` export (grep `src/`), and `git status` in `frontend/` shows only the intended files changed (package files, `src/api/`, `.oxlintrc.json`, `README.md`, plus the new `src/api/generated/`)
