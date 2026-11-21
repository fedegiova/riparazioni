# Tasks

## 1. Imaging dependency

- [x] 1.1 Add `pillow` to `requirements.txt` and install it in the dev venv; verify `python -c "import PIL"` succeeds and `pip install -r requirements.txt` completes.

## 2. Resize and minified derivative in the picture service

- [x] 2.1 In `app/services/pictures.py`, decode each upload with Pillow, apply `ImageOps.exif_transpose`, downscale to a longest edge of at most 2880 px with `Image.thumbnail` (never enlarging a smaller image), store the resized bytes under the existing `<owner_type>/YYYY-MM-DD-SEQ` naming with the extension from the decoded format, and reject a file Pillow cannot decode with a 400 that stores neither a record nor a file; verify `tests/test_api_pictures.py` covers a large image being downscaled to ≤ 2880, a small image keeping its dimensions, the decoded-format extension, and a non-image upload returning 400 with nothing stored.
- [x] 2.2 In `app/services/pictures.py`, build a ≤ 320 px longest-edge minified derivative beside the original as `<owner_type>/YYYY-MM-DD-SEQ.thumb.<ext>` during upload and record its path, and make picture deletion remove both the full file and the derivative; verify `tests/test_api_pictures.py` asserts the derivative exists at ≤ 320 px and that deleting a picture removes both files.

## 3. Model column and migration

- [x] 3.1 In `app/models/owned.py`, give `Picture` a nullable, unique `thumbnail_path` column, and create the Alembic revision on `c8d7e6f5a4b3` that adds it (batch-safe on SQLite, plain add on MSSQL); verify `pytest tests/test_migration.py` reaches head and `flask dev-init --reset` succeeds.

## 4. Thumbnail endpoint and lazy backfill

- [x] 4.1 Add `GET /api/v1/pictures/<id>/thumbnail` in `app/routes/api/pictures.py`, serving the derivative bytes with an image content type through the existing `resolve_path` traversal guard; when a picture has no derivative (a row stored before this change) derive it from the stored file, record the column, and serve it, and return 404 for an unknown id; verify `tests/test_api_pictures.py` covers the download, the lazy backfill recording the column, and the unknown-id 404.

## 5. API contract, generated client, and docs

- [x] 5.1 Add the `/api/v1/pictures/{picture_id}/thumbnail` path to `docs/openapi.yaml` and regenerate the frontend client (`npm run generate:api`); verify `pytest tests/test_openapi_contract.py` passes and `npm run build` type-checks.
- [x] 5.2 Update the README Pictures section to document the 2880 px resize, the minified view, the `/thumbnail` endpoint, and the non-image 400; verify the documented paths and behaviors match the implemented routes.

## 6. Frontend pictures API wrapper

- [x] 6.1 Add `pictureThumbnailUrl(id)` (`/api/v1/pictures/<id>/thumbnail`) to `frontend/src/api/pictures.ts`, mirroring `pictureFileUrl`; verify `frontend/src/api/pictures.test.ts` covers the returned URL.

## 7. Shared full-screen picture gallery

- [x] 7.1 Add `yet-another-react-lightbox` to `frontend/package.json` (`npm install yet-another-react-lightbox`) and import its stylesheet once; verify `npm install` and `npm run build` succeed.
- [x] 7.2 Create `frontend/src/components/PictureGallery.tsx` as a thin wrapper over the library: map the ordered pictures to slides with `pictureFileUrl` (full-size, not the thumbnail), open at the activated index, configure non-wrapping navigation (the carousel `finite` option) and show no navigation for a single picture; verify `frontend/src/components/PictureGallery.test.tsx` covers the slides mapped from the full-size URL, opening at the activated index, the close callback, and the single-picture case, asserting the wrapper's contract rather than the library's internals.

## 8. Reusable picture section

- [x] 8.1 Create `frontend/src/components/PictureSection.tsx` taking `ownerType`, `ownerId`, and optional `initialPictures`: render the hidden `<input type="file" accept="image/*" capture="environment">` capture control, the thumbnail grid loaded from `pictureThumbnailUrl`, a per-picture delete, an error alert, and the `PictureGallery`; seed state from `initialPictures` when given, otherwise load with `listPictures(ownerType, ownerId)` on mount and on owner change, and append uploads via `uploadPicture` and remove deletes via `deletePicture` (reusing the existing mobile-safe handling in `frontend/src/api/pictures.ts`); verify `frontend/src/components/PictureSection.test.tsx` covers the on-demand fetch, capture-upload, thumbnails asserting the thumbnail URL, delete, and opening the gallery from a thumbnail.

## 9. Repair page gallery

- [x] 9.1 Replace the inline pictures markup in `frontend/src/pages/RepairPage.tsx` with `PictureSection` (passing the repair detail's pictures as `initialPictures`, rendered only when the repair exists) so its thumbnails open the full-screen gallery; verify the existing capture/thumbnails/delete cases in `frontend/src/pages/RepairPage.test.tsx` still pass and a new case opens a thumbnail full screen and scrolls to the next repair picture.

## 10. Spare-part pictures in the warehouse UI

- [x] 10.1 In `frontend/src/components/PartsManager.tsx`, add a per-row **Pictures** action that opens a dialog rendering `PictureSection` with `ownerType="spare"` and the part id, and render a `PictureSection` inside the existing New/Edit dialog only when editing a saved part; verify `frontend/src/components/PartsManager.test.tsx` covers opening the row dialog and fetching that part's pictures, capturing/uploading for a spare, deleting a picture, the edit dialog showing pictures for an existing part, and a new part offering no picture controls.
- [x] 10.2 Confirm the refrigerator-parts tab reuses the same picture behavior (both tabs render `PartsManager`); verify `frontend/src/pages/MagazzinoPage.test.tsx` still passes with the added row action and no regressions to the part create/edit/delete flows.

## 11. Cylinder pictures in the warehouse UI

- [x] 11.1 In `frontend/src/components/CylindersManager.tsx`, add a per-row **Pictures** action that opens a dialog rendering `PictureSection` with `ownerType="cylinder"` and the cylinder id, and render a `PictureSection` inside the existing New/Edit dialog only when editing a saved cylinder; verify `frontend/src/components/CylindersManager.test.tsx` covers the row dialog fetching and showing that cylinder's pictures, capture/upload, delete, the edit dialog showing pictures for an existing cylinder, a new cylinder offering no picture controls, and that the existing row actions (Log, Edit, Refill, Archive/Restore, Delete) are unchanged.

## 12. Integration verification

- [x] 12.1 Run the backend and frontend suites and static checks (`pytest`, and in `frontend/` `npm test`, `npm run lint`, `npm run build`); verify all exit 0 and that a large upload is stored at ≤ 2880 px with a working `/thumbnail`, and that the repair-page and warehouse picture flows work end to end.

## 13. Lightbox zoom and pan

- [x] 13.1 Register the `yet-another-react-lightbox/plugins/zoom` plugin in `frontend/src/components/PictureGallery.tsx` (pinch, double-tap/double-click, and wheel zoom with drag-to-pan) and set `maxZoomPixelRatio: 3` so zoom works past the default 1:1 cap on the repair and parts/cylinder picture views; verify `frontend/src/components/PictureGallery.test.tsx` asserts the plugin and its wheel-zoom and max-zoom options are passed to the library.
