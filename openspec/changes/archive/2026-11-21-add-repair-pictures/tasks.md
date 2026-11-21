# Tasks

## 1. Schema and models

- [x] 1.1 In `app/models/owned.py`, give `Picture` the `owner_type` (String, NOT NULL) and `owner_id` (Integer, NOT NULL) columns, drop its `cylinders`/`parts` relationships, and remove `picture_ref` from `GasCylinder` and `ServicePart` (including `to_dict`); verify `pytest tests/test_models.py` (with new assertions for the owner columns and the absence of `picture_ref`) passes.
- [x] 1.2 Create the Alembic revision (revises `b7c2e9f14a06`) that adds `owner_type`/`owner_id` as NOT NULL and drops the `picture_ref` foreign keys and columns from `GAS_CYLINDERS` and `SERVICE_PARTS`; there are no existing picture rows, so no backfill or data migration is needed (batch-safe on SQLite, FKs dropped first on MSSQL); verify `flask dev-init --reset` reaches head and `pytest tests/test_migration.py` passes.

## 2. Picture storage service

- [x] 2.1 Rewrite `app/services/pictures.py` so `store_upload` requires `owner_type`/`owner_id`, writes to `UPLOAD_DIR/<owner_type>/YYYY-MM-DD-SEQ.<ext>` with a per-type/per-day zero-padded sequence (extension preserved from the upload, no caller-supplied name), and relies on a unique constraint on `PICTURES.path` with a retry on `IntegrityError`; verify `pytest tests/test_api_pictures.py` storage cases cover the name pattern, the per-type folder, sequence increments within a type/day, and extension preservation.
- [x] 2.2 Validate the owner in the service: reject an owner type outside `repair`/`spare`/`cylinder` and a missing owner id with 400, and a non-existent owner id with 409 (reusing the per-model lookups); verify tests for an unknown type and an unknown owner id, each creating no record.

## 3. Pictures API

- [x] 3.1 Update `app/routes/api/pictures.py`: `POST` reads `owner_type`/`owner_id` from the multipart form and passes them through, `GET` accepts an optional `owner_type`+`owner_id` pair (one without the other is 400; both filter the list; neither returns all), and `DELETE` no longer depends on references; verify `pytest tests/test_api_pictures.py` covers upload-with-owner 201, by-owner filtering, incomplete-filter 400, and delete of a referenced picture returning 204 with record and file gone.
- [x] 3.2 Update the README "Pictures" section (and the delete/`picture_ref` notes) to the owner-based upload, the `<type>/YYYY-MM-DD-SEQ` layout, the by-owner listing, and the removal of the 409 delete; verify the documented paths and behaviors match the implemented routes.

## 4. Repair detail pictures

- [x] 4.1 In `app/services/repairs.py`, attach a `pictures` array (that repair's pictures, ordered by id) to the single-repair serialization alongside `work_log` and `parts`, leaving the list response shape unchanged; verify `pytest tests/test_api_repairs.py` asserts the detail includes the repair's pictures and the list response does not.

## 5. OpenAPI contract and generated client

- [x] 5.1 Update `docs/openapi.yaml`: the upload request body (`owner_type`, `owner_id` required), the `Picture` schema (owner fields), the by-owner query parameters on `GET /pictures`, `RepairDetail.pictures`, and the removal of `picture_ref` from the cylinder/part schemas; verify `pytest tests/test_openapi_contract.py` passes.
- [x] 5.2 Regenerate the frontend client (`npm run generate:api`) and confirm the new types; verify `npm run build` type-checks.

## 6. Frontend pictures API wrapper

- [x] 6.1 Add `frontend/src/api/pictures.ts` (`uploadPicture(file, ownerType, ownerId)` as `FormData`, `listPictures(ownerType, ownerId)`, `deletePicture(id)`, `pictureFileUrl(id)`) and the corresponding re-exports in `frontend/src/api/types.ts`; verify `frontend/src/api/pictures.test.ts` covers the multipart upload payload, the owner query, and delete.

## 7. Frontend repair page pictures section

- [x] 7.1 Add a Pictures section to `frontend/src/pages/RepairPage.tsx`, rendered only when the repair exists: a capture control backed by a hidden `<input type="file" accept="image/*" capture="environment">` that uploads with no filename prompt, a thumbnail grid from `pictureFileUrl`, a per-picture delete, and error surfacing; verify `frontend/src/pages/RepairPage.test.tsx` covers capture-upload, thumbnails, and delete.

## 8. Integration verification

- [x] 8.1 Run the full backend and frontend suites and lint

## 9. Fix uploads from a device that omits the filename

- [x] 9.1 Always append a fallback filename
- [x] 9.2 In `frontend/src/pages/RepairPage.tsx`, clear the file input only after the upload completes
- [x] 9.3 In `frontend/src/api/pictures.ts`, read the picked/captured file into an in-memory File before upload (Firefox for Android fails a `fetch` that streams a camera `File` backed by a `content://` URI); verify `frontend/src/api/pictures.test.ts` covers the materialized bytes and `npm run build` passes. (resetting `input.value` before the async read invalidates the File on mobile and fails the fetch with a network error); verify `frontend/src/pages/RepairPage.test.tsx` still covers the capture-upload path and `npm run build` passes. in `frontend/src/api/pictures.ts` (`form.append('file', file, file.name || 'photo.jpg')`) and, in `app/services/pictures.py`, reject only when the file part is absent while deriving the extension from the filename or the part's MIME type; verify the new backend cases pass (empty `filename` → 201 with a MIME-derived extension, missing `filename`/no part → 400) and a frontend case asserts the fallback name is used when `file.name` is empty. (`pytest`, `npm test`, `npm run lint`, `npm run build`); verify all exit 0 and that the `equipment` behaviors retained from the archived warehouse change (archive, refill, required `full_weight`) still match the implemented model.
