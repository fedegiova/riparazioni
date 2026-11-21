# Proposal

## Why

Technicians photograph repairs from a tablet, but the pictures can only be seen
as 120×120 thumbnails: there is no way to open one full screen or move between
the photos of a record, which makes them hard to read on a small screen. Spare
parts and gas cylinders can already own pictures in the database and through the
API, yet the warehouse screens have no picture UI at all, so those photos can
never be captured or viewed. On top of that, uploads keep the camera's
full-resolution bytes (often several megabytes), so grids and full-screen views
download far more data than they display.

## What Changes

- Add a reusable **full-screen picture viewer** built on the
  `yet-another-react-lightbox` library (MIT, zero-dependency, React 19): opening
  a thumbnail shows the picture full screen with a close control and lets the
  user move between the pictures of the current collection (previous/next
  controls, keyboard arrows, and swipe).
- Make the **repair page** thumbnails open that viewer at the tapped picture.
- Add a **pictures UI to spare parts and gas cylinders** in the warehouse
  screen, covering both regular and refrigerator parts:
  - a per-row **Pictures** action that opens a dialog with the record's
    thumbnails and the full-screen viewer (view-focused entry point);
  - a **Pictures** area inside the existing New/Edit dialog for adding
    (capture from the device camera, no filename prompt), deleting, and viewing
    the record's pictures (edit-focused entry point).
- Load equipment pictures on demand from the existing
  `GET /api/v1/pictures?owner_type=&owner_id=` endpoint (the `pictures`
  capability already accepts the `spare` and `cylinder` owner types).
- **Resize on upload**: the server stores the uploaded image resized so its
  longest edge is at most **2880 px**, preserving aspect ratio and orientation;
  the original full-resolution bytes are not kept.
- **Minified view on upload**: upload also stores a **≤ 320 px** longest-edge
  derivative, served at a new `GET /api/v1/pictures/<id>/thumbnail`; the picture
  grids load that derivative, and the full-screen gallery shows the resized full
  image.
- **Reject non-images**: an upload the server cannot decode as an image is
  rejected with HTTP 400 and stores nothing.
- Add the **Pillow** dependency for decoding and resizing.
- Pictures stored before this change keep their existing file and have their
  minified view generated lazily on first request.

## Capabilities

### New Capabilities
- `picture-gallery`: the reusable full-screen picture viewer — display a loaded
  picture's full stored image full screen and scroll between the pictures of the
  current collection.

### Modified Capabilities
- `pictures`: uploads are decoded and resized to a 2880 px longest edge, a
  ≤ 320 px minified derivative is stored and served, and a non-image upload is
  rejected.
- `repairs-ui`: the repair page's picture thumbnails open the full-screen
  gallery and scroll between the repair's pictures.
- `warehouse-ui`: spare parts and gas cylinders gain a picture UI — capture,
  list as thumbnails, delete, and open in the full-screen gallery — reachable
  from a per-row dialog and from the New/Edit dialog.

## Impact

- Backend: `app/services/pictures.py` (decode, resize to 2880, build the
  ≤ 320 px derivative, reject non-images, delete both files), `app/routes/api/pictures.py`
  (the thumbnail route), `app/models/owned.py` (`Picture.thumbnail_path`), a new
  Alembic revision for the column, and `requirements.txt` (Pillow).
- API contract: `docs/openapi.yaml` gains `GET /api/v1/pictures/<id>/thumbnail`,
  and the frontend client is regenerated; the `Picture` response shape is
  unchanged.
- Frontend: new shared components under `frontend/src/components/` (a
  full-screen viewer wrapping the lightbox and a reusable picture section) used
  in `frontend/src/pages/RepairPage.tsx`, `frontend/src/components/PartsManager.tsx`,
  and `frontend/src/components/CylindersManager.tsx`; `frontend/src/api/pictures.ts`
  gains a `pictureThumbnailUrl(id)` helper for grids.
- Frontend dependency: add `yet-another-react-lightbox` (MIT, zero runtime
  dependencies, React 19) to `frontend/package.json` for the full-screen viewer.
- Tests: backend cases in `tests/test_api_pictures.py` (resize, derivative,
  non-image 400, delete removes both, lazy backfill), `tests/test_migration.py`,
  `tests/test_openapi_contract.py`, plus new/updated Vitest component and page
  tests for the gallery, the thumbnail URL, and the equipment picture UI.
- Deployment: Pillow must be installed on the host (wheel-provided libjpeg);
  the backend deploy precedes the frontend.
