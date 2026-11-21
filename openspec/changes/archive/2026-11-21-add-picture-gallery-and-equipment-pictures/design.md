# Design

## Context

See `proposal.md` — Why. Constraints that shape the approach:

- The frontend is a React 19 + MUI SPA (`frontend/`) served same-origin. MUI has
  no lightbox component (only `Dialog`/`Modal`, `ImageList`, `Backdrop`), and
  `package.json` has no lightbox dependency; this change adds
  `yet-another-react-lightbox` (MIT, zero runtime dependencies, supports React
  19) for the full-screen viewer.
- `frontend/src/api/pictures.ts` already exposes
  `uploadPicture(file, ownerType, ownerId)`, `listPictures(ownerType, ownerId)`,
  `deletePicture(id)`, and `pictureFileUrl(id)`; `ownerType` is already
  `'repair' | 'spare' | 'cylinder'` and `Picture` is already a generated type.
- The backend `GET /api/v1/pictures?owner_type=&owner_id=` already filters by
  owner and orders by id, and accepts `spare`/`cylinder`. Equipment responses do
  not embed pictures, and the warehouse managers read list responses only.
- No imaging library is installed (`requirements.txt` has no Pillow); uploads
  store the raw multipart bytes as-is (`app/services/pictures.py`
  `store_upload`). `PICTURES` has no derivative column. The current Alembic head
  is `c8d7e6f5a4b3` (pictures owner).
- `tests/test_openapi_contract.py` asserts that every `/api/v1` route is
  documented, so a new picture route must be added to `docs/openapi.yaml` and
  the generated client regenerated.
- The repair page (`RepairPage.tsx`) renders its pictures from the repair
  detail's embedded `pictures` array (state seeded in a `useEffect`) with a
  hidden `<input type="file" accept="image/*" capture="environment">`, a
  thumbnail grid, a per-picture delete, and the mobile-safe upload handling in
  `pictures.ts`.
- `PartsManager.tsx` (used for both Ricambi and Ricambi Frigo) is a table plus a
  New/Edit dialog; `CylindersManager.tsx` is a table with row actions plus a
  New/Edit dialog and a refill dialog. A record has no id until it is saved.

## Goals / Non-Goals

**Goals:**

- One reusable full-screen picture viewer with previous/next, keyboard, and
  swipe navigation that any picture collection can use.
- One reusable picture section (capture, thumbnails, delete, gallery) so the
  repair page and the two equipment managers share behavior instead of
  duplicating it.
- Add the picture section to spare parts and gas cylinders with two entry
  points: a per-row dialog and the New/Edit dialog.
- Resize every uploaded image to a 2880 px longest edge and store a ≤ 320 px
  minified derivative for fast grids, with a non-image upload rejected.

**Non-Goals:**

- Embedding pictures in equipment list/detail responses.
- A live `getUserMedia` viewfinder (the file-input capture stays).
- Picture reordering, captions, or upload progress bars (the existing
  "uploading" disabled state stays).
- Retroactively resizing the full-size file of pictures stored before this
  change (only their minified view is generated lazily).
- Preserving animation in animated GIFs (photos are the target input).
- Sharing a picture between records.

## Decisions

### D1. Full-screen viewer via `yet-another-react-lightbox`

`frontend/src/components/PictureGallery.tsx` is a thin wrapper over
`yet-another-react-lightbox`, mapping the ordered `Picture[]` to `slides`
(`{ src: pictureFileUrl(id) }`) and opening at the activated index. The library
provides the full-screen overlay, close control, keyboard arrows, and swipe;
non-wrapping is configured with the carousel's `finite` option, and a
single-picture collection shows no navigation. Its stylesheet is imported once.

The wrapper keeps the rest of the app decoupled from the library (one place to
swap it) and gives the viewer more than a hand-rolled one: preloading and
zoom/pan. Zoom is a separate library plugin, so the wrapper registers
`yet-another-react-lightbox/plugins/zoom` (pinch, double-tap/double-click, and
wheel zoom, with drag-to-pan); without it the library offers no zoom at all.
For image slides the plugin caps zoom at the image's native resolution
(`maxZoomPixelRatio` defaults to 1; its `maxZoom` option applies only to custom
slide types), so the wrapper sets `maxZoomPixelRatio: 3` to allow magnifying up
to three times native — useful because uploads are capped at a 2880 px edge.

Alternatives rejected: composing MUI `Dialog`/`Modal` + `IconButton` by hand (no
zoom/pan/preloading and ~100 lines plus tests to own; MUI has no lightbox
component), `react-photo-view` (unclear React 19 support, last release Jan
2025), and `lightGallery` (GPLv3/commercial licensing for a closed internal
app).

### D2. Reusable `PictureSection` for capture, list, delete, and gallery

`frontend/src/components/PictureSection.tsx` owns a picture list and renders the
capture control (hidden file input), the thumbnail grid, per-picture delete,
the error alert, and the `PictureGallery`. Props: `ownerType`, `ownerId`, and an
optional `initialPictures`.

- When `initialPictures` is supplied (the repair page, which already has the
  pictures from the repair detail), it seeds state and no extra request is made.
- When it is not supplied (spare parts and cylinders), the component loads with
  `listPictures(ownerType, ownerId)` on mount and whenever the owner changes.

Uploads append via `uploadPicture` and deletes via `deletePicture`, reusing the
existing mobile-safe behavior in `pictures.ts` (materialized File, input cleared
after upload). This keeps the repair page's current data flow and tests intact
while giving equipment an on-demand fetch.

### D3. Equipment pictures: on-demand fetch, two entry points

Spare parts and cylinders do not embed pictures, so the section fetches them
with `listPictures` for the selected record. Two entry points are provided, per
the chosen scope:

- **Row dialog**: a Pictures action on each row opens a `Dialog` whose content
  is a `PictureSection` for that record — the view-first path.
- **Edit dialog**: the existing New/Edit dialog renders a `PictureSection` when
  editing a saved record. For a new record (no id yet) the area is not offered;
  the user saves first. This mirrors how the repair page only shows its pictures
  section once the repair exists.

Both use the same component, so there is no duplicated picture logic.

### D4. Owner types and ordering

Spares use `ownerType="spare"`, cylinders `"cylinder"`, matching
`app/services/pictures.py` `OWNER_TYPES` and the generated `Picture.owner_type`
enum. Pictures are shown in the order the API returns (ascending id, as the
by-owner list orders them), so the gallery's previous/next order matches the
thumbnail order.

### D5. Resize on upload with Pillow

`app/services/pictures.py` gains an image step: decode the upload with Pillow,
apply `ImageOps.exif_transpose` so camera orientation is baked in, and downscale
with `Image.thumbnail((2880, 2880))` (a no-op when the image already fits, so
small images are never enlarged). The resized bytes are what gets stored; the
original full-resolution bytes are discarded. The stored extension comes from
the decoded image's format (`Image.format`), not the client filename, and the
format is preserved (JPEG stays JPEG, PNG stays PNG). An upload Pillow cannot
decode raises a 400 and stores nothing.

Alternatives rejected: keeping the original and only resizing on read (defeats
the storage/bandwidth goal), a client-side resize (unreliable across devices and
not authoritative), and adding `pillow-heif` (deferred — HEIC is rejected with a
clear 400 for now, see Risks).

### D6. Minified derivative, stored and served by id

Upload also writes a second file derived from the resized image, downscaled with
`Image.thumbnail((320, 320))`, next to the original as
`<owner_type>/YYYY-MM-DD-SEQ.thumb.<ext>`. `PICTURES` gains a nullable, unique
`thumbnail_path` column (legacy rows are null); a new Alembic revision on
`c8d7e6f5a4b3` adds it. The derivative is served at
`GET /api/v1/pictures/<id>/thumbnail`, which reuses the existing
`resolve_path` traversal guard. When a picture has no derivative (a row stored
before this change), the route derives it from the stored file, records the
column, and serves it — the lazy backfill. Deleting a picture removes both the
full file and the derivative.

Alternatives rejected: deriving the derivative path from `path` with no column
(works, but the chosen option records it explicitly and keeps the schema
self-describing), and generating the thumbnail per request without storing it
(per-request CPU and no cacheable artifact).

### D7. Frontend loads the right rendition

`frontend/src/api/pictures.ts` gains `pictureThumbnailUrl(id)`
(`/api/v1/pictures/<id>/thumbnail`), mirroring `pictureFileUrl`. The thumbnail
grids (`PictureSection`) use it; the full-screen `PictureGallery` uses
`pictureFileUrl(id)` so it shows the resized full image. No `Picture` field is
added to the API response — the URL is derived from the id, so the `Picture`
schema and the repair-detail shape are unchanged.

## Risks / Trade-offs

- **[Per-record request when opening equipment pictures]** The section fetches
  on demand, so opening a record's pictures costs one request. → Acceptable:
  lists stay lean, and the request only happens when the user opens the record's
  pictures.
- **[Swipe vs. button taps]** A naive touch handler can swallow taps or fire on
  vertical scroll. → Use a horizontal distance threshold and ignore gestures
  below it; keyboard/buttons remain as non-touch paths.
- **[Repair page behavior drift]** Extracting the repair pictures UI into a
  shared component could change its data flow. → The repair page passes its
  detail-provided pictures as `initialPictures`, preserving the current
  no-extra-request behavior and its existing tests.
- **[Large photos on a small screen]** Full-screen `contain` may letterbox very
  wide/tall photos. → Accepted; the goal is a readable, non-cropped view.
- **[Lightbox adds a second styling system and bundle weight]** The library ships
  its own CSS and code. → The core is tree-shakeable and has zero runtime
  dependencies; import its stylesheet once in the wrapper, and keep the wrapper
  the only consumer so a future swap touches one file.
- **[Testing the viewer in jsdom]** The library renders through a portal and
  preloads images, which jsdom does not fully emulate. → Test the wrapper's
  contract (slides mapped from `pictureFileUrl`, open index, close callback, and
  that the full-size URL is used) rather than the library's internals.
- **[Third-party maintenance]** A library can lag React releases. → It states
  React 19 support and is actively maintained (Oct 2026); the wrapper isolates a
  replacement if needed.
- **[HEIC uploads are rejected]** Pillow cannot decode HEIC/HEIF, which some
  iOS camera-roll selections produce, so those uploads fail with a 400. → The
  file-input capture path usually yields JPEG; surface a clear error. Adding
  `pillow-heif` is a tracked follow-up, not part of this change.
- **[Dev-only camera upload failure under Vite HMR]** Taking a photo from
  Firefox for Android backgrounds the tab; when the HMR WebSocket reconnects,
  Vite reloads the page and aborts the in-flight upload (the backend sees a
  truncated body and logs `ClientDisconnected`). → Dev-only: the production
  build has no HMR. Test mobile camera uploads against the built app or set
  `server.hmr: false`; the storage picker is unaffected.
- **[Memory on huge images]** Decoding a very large photo can use a lot of
  memory per request. → Resize with `Image.thumbnail` (streamed downscale) and
  keep the existing 50 MB nginx upload cap; revisit only if real photos approach
  that size.
- **[Legacy full images stay large]** Only new uploads are resized; pictures
  stored earlier keep their original file (only their derivative is backfilled).
  → Accepted and bounded: the endpoint already serves them; a one-off backfill
  can be added later if needed.
- **[Animated GIF loses animation]** Downscaling a multi-frame GIF keeps one
  frame. → Accepted: photos are the target input; GIFs are not part of the
  capture flow.
- **[Pillow must be installed on the host]** The app will fail to import without
  it. → Add it to `requirements.txt` and install during the backend deploy
  (wheels bundle libjpeg); deploy the backend before the frontend.
- **[Overlapping in-flight change on `CylindersManager.tsx`]**
  `add-cylinder-operation-log` also edits `CylindersManager.tsx` (it adds the
  per-row Log control and the `/magazzino/bombole/:id` route). → Apply the
  picture additions after that change lands, or rebase them onto its row
  actions; the picture action is additive and does not alter the existing
  controls.

## Migration Plan

1. Add Pillow to `requirements.txt` and install it (host and dev venv).
2. Backend: resize + derivative in `app/services/pictures.py` (non-image → 400,
   delete removes both files), the `thumbnail_path` column, a new Alembic
   revision on `c8d7e6f5a4b3` (nullable/unique; SQLite `batch_alter_table`,
   MSSQL plain add), and `GET /api/v1/pictures/<id>/thumbnail` with the lazy
   legacy backfill. Run `alembic upgrade head`; dev replays it via
   `make dev-init`.
3. Update `docs/openapi.yaml` (the thumbnail path) and regenerate the frontend
   client (`npm run generate:api`); update the README Pictures section.
4. Frontend: `npm install yet-another-react-lightbox`, add
   `pictureThumbnailUrl` and the shared `PictureGallery`/`PictureSection`
   components, then wire them into `RepairPage.tsx` (with `initialPictures`),
   `PartsManager.tsx`, and `CylindersManager.tsx`.
5. Deploy the backend first (new route and resized storage), then the frontend.
   Rollback: revert the frontend, then the backend; the column and derivative
   files are additive, so downgrading the migration drops the column and any
   leftover `.thumb.` files are simply ignored.
