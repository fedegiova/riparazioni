# Proposal

## Why

A technician working on a repair needs to photograph the unit from a tablet and
have the pictures kept with the repair record. The `pictures` capability already
stores and serves files, but nothing in the application can capture a photo, and
the only ownership the database knows is a single `picture_ref` on gas cylinders
and service parts — one picture each, unrelated to repairs. This change lets the
workshop attach an arbitrary number of dated photos to a repair and capture them
directly from the tablet camera.

## What Changes

- Add a **Pictures** section to the repair page: a camera control that opens the
  tablet camera (plain file input with `accept="image/*" capture="environment"`,
  no filename prompt) and a thumbnail list with a delete control.
- **BREAKING**: picture upload now requires an owner. `POST /api/v1/pictures`
  takes `owner_type` (`repair` | `spare` | `cylinder`) and `owner_id`; a picture
  is always attached to exactly one record at upload time and is never shared.
- **BREAKING**: change the storage layout from
  `UPLOAD_DIR/pictures/<uuid>.<ext>` to a **per-type folder** named
  `UPLOAD_DIR/<type>/YYYY-MM-DD-SEQ.<ext>`, where `SEQ` is a per-type, per-day
  sequence. The root stays the configurable `UPLOAD_DIR`.
- Give `PICTURES` an `owner_type` + `owner_id` pair (patch the existing table;
  no junction table), and list a picture by owner
  (`GET /api/v1/pictures?owner_type=&owner_id=`).
- Include the repair's pictures in the repair detail response (a `pictures`
  array alongside `work_log` and `parts`).
- **BREAKING**: remove `picture_ref` from `GAS_CYLINDERS` and `SERVICE_PARTS`;
  cylinder/part photos are found through the owner columns instead.
- **BREAKING**: deleting a picture no longer returns 409. A picture always
  belongs to exactly one owner, so deletion removes it from that owner.

## Capabilities

### New Capabilities
<!-- None: the behavior extends existing capabilities. -->

### Modified Capabilities
- `pictures`: upload requires an owner and uses the per-type `YYYY-MM-DD-SEQ`
  layout; add listing by owner; delete is no longer blocked by references.
- `equipment`: gas cylinders and service parts drop the single `picture_ref`
  field; their photos are owned through the pictures capability.
- `repairs`: the single-repair detail response also includes the repair's
  pictures.
- `repairs-ui`: the repair page gains a pictures section (capture from the
  tablet camera, thumbnails, delete).

## Impact

- Backend: `app/models/owned.py` (`Picture` gains `owner_type`/`owner_id` and
  loses its cylinder/part relationships; `GasCylinder`/`ServicePart` lose
  `picture_ref`), `app/services/pictures.py` (owner-aware naming and sequence,
  path building, owner validation), `app/routes/api/pictures.py` (owner
  parameters and the by-owner filter), `app/services/repairs.py` +
  `app/routes/api/repairs.py` (attach pictures to repair detail), and a new
  Alembic migration that adds the owner columns (`NOT NULL`) and drops
  `picture_ref` — there are no existing pictures, so no data migration is
  needed.
- API contract: `docs/openapi.yaml` (upload request, `Picture` schema, by-owner
  query, `RepairDetail.pictures`, removed `picture_ref`) and the regenerated
  frontend client.
- Frontend: new `frontend/src/api/pictures.ts`, a Pictures section in
  `frontend/src/pages/RepairPage.tsx`, the regenerated
  `frontend/src/api/generated/schema.d.ts`, page/api tests.
- Tests: `tests/test_api_pictures.py` (owner, naming, no-409 delete),
  `tests/test_api_repairs.py` (detail pictures), `tests/test_openapi_contract.py`,
  `tests/test_migration.py`, plus frontend page/api tests.
- Config: reuses the existing `UPLOAD_DIR`; no new environment variable. The
  tablet capture requires no HTTPS because it uses a file input, not
  `getUserMedia`.
