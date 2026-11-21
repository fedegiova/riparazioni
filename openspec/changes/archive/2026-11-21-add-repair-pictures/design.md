# Design

## Context

See `proposal.md` — Why. Constraints that shape the approach:

- The `pictures` capability exists (`app/models/owned.py` `Picture`,
  `app/services/pictures.py`, `app/routes/api/pictures.py`,
  `tests/test_api_pictures.py`): files at `UPLOAD_DIR/pictures/<uuid4-hex><ext>`,
  a single `picture_ref` FK on `GasCylinder`/`ServicePart`, and delete-409
  enforced by those FKs with `passive_deletes`.
- Owned tables are lowercase, created only by Alembic migrations; production is
  MSSQL, dev/tests are SQLite (`migrations/env.py` owns only the app tables).
  `UPLOAD_DIR` is already the configurable runtime directory.
- The frontend is a React + MUI SPA whose API is generated from
  `docs/openapi.yaml` (`npm run generate:api`), served same-origin behind nginx.
  The repair page already renders `parts` and `work_log` sections from the
  repair detail; a new repair has no id until saved, so add-on sections render
  only when `!isNew`.
- `Picture` is not referenced by any UI today; the only producers are manual API
  calls/tests, so no picture rows exist in practice.
- `add-warehouse-management` is archived; its wording (the cylinder archive and
  refill requirements, the `archived flag`, the required `full_weight`) is the
  current base this change's `equipment` delta modifies.

## Goals / Non-Goals

**Goals:**

- Capture a photo from a tablet and attach an arbitrary number of photos to a
  repair, stored under the configurable `UPLOAD_DIR` as
  `<type>/YYYY-MM-DD-SEQ.<ext>`.
- One ownership model (`PICTURES.owner_type`/`owner_id`) that covers repairs,
  spares, and cylinders, replacing the single `picture_ref`.
- Keep the capture working over plain HTTP with no extra dependency.

**Non-Goals:**

- A live in-app viewfinder (`getUserMedia`) or any HTTPS-only capture path.
- Sharing one picture across owners, or a polymorphic junction table.
- A spare/cylinder picture UI (the model supports all three types; only the
  repair page gets capture in this change).
- Attaching pictures to individual work-log entries (the owner is the repair).
- Server-side resizing/thumbnailing or HEIC transcoding.

## Decisions

### D1. Owner columns on `PICTURES`, one owner per picture

`PICTURES` gains `owner_type` (string) and `owner_id` (integer), both NOT NULL,
and loses its `cylinders`/`parts` relationships. A picture belongs to exactly one
record and is created already attached.

Alternatives rejected: a polymorphic `PICTURE_LINKS` junction table (unneeded —
no sharing, and attach-at-upload removes the unowned window), per-entity join
tables (a migration per entity), or `owner_type`/`owner_id` on each owner table
(duplicated, unbounded lists).

### D2. Drop `picture_ref` from gas cylinders and service parts

With owners on `PICTURES`, keeping a single `picture_ref` would be a second,
contradictory mechanism (it could point at a picture owned by a repair). Both
columns and their FKs are removed; a cylinder's/part's photos are the pictures
whose owner is that row.

### D3. Owner type is a validated string, not a DB enum

`owner_type` accepts `repair`, `spare`, `cylinder`. Validation lives in the
service layer (a set membership check), mirroring how `gas_system_state` is a
plain string. This extends the vocabulary without a migration and avoids MSSQL vs
SQLite `CHECK`/enum divergence.

### D4. Per-type `YYYY-MM-DD-SEQ` naming with a unique index and retry

Files are written to `UPLOAD_DIR/<owner_type>/YYYY-MM-DD-SEQ.<ext>`; `SEQ` is a
per-`(owner_type, day)` counter zero-padded to four digits. The next value is
derived from the highest existing sequence for that type and day, and the insert
is retried on a unique-constraint violation on `PICTURES.path`.

```
tablets upload concurrently         repair/2026-11-21-0003.jpg  (unique on path)
        |                                     ^ retry guard on IntegrityError
        v                                     |
   MAX(seq for type+day) + 1  -->  insert  --+--> commit
```

`PICTURES.path` carries a unique index, which is the real collision guard; the
computed name is only a hint. Alternatives rejected: a counter table with `SELECT
... FOR UPDATE` (MSSQL-specific locking), a filesystem scan for the max
(racy), and a UUID name (does not meet the requested naming).

### D5. Name from the server, extension from the upload

`YYYY-MM-DD` comes from the server clock and `SEQ` from the database; the
extension is derived from the uploaded filename via `secure_filename`. The user
is never asked for a name. The `path` column stays relative to `UPLOAD_DIR` and
`resolve_path` keeps the existing traversal guard.

### D6. API surface

- `POST /api/v1/pictures` (multipart) requires `file`, `owner_type`, `owner_id`;
  an unknown type is 400, a non-existent owner id is 409, and `uploaded_by`
  stays optional.
- `GET /api/v1/pictures?owner_type=&owner_id=` filters by owner; supplying only
  one of the two is 400. No filter keeps returning all pictures.
- `GET /pictures/<id>` and `/file` are unchanged; `DELETE /pictures/<id>` no
  longer 409s.

The owner existence check reuses the existing per-model `db.session.get` lookups,
consistent with the 409 convention already used for unknown customers/vehicles.

### D7. Pictures ride on the repair detail response

The repairs service attaches a `pictures` array to the single-repair
serialization, alongside `work_log` and `parts`, so the repair page renders the
list without an extra request. The by-owner list endpoint remains for other
callers.

### D8. Frontend capture uses a plain file input

A hidden `<input type="file" accept="image/*" capture="environment">`, triggered
by a button, opens the tablet camera; the same control accepts a chosen file on
desktop. The file is POSTed as `FormData` with `owner_type=repair` and the
repair id, then the detail is reloaded. Thumbnails load from
`/api/v1/pictures/<id>/file`. No HTTPS or permission handling is needed, unlike
`getUserMedia`. The section renders only when the repair exists.

### D9. Migration adds the owner columns and drops `picture_ref`

Add `owner_type`/`owner_id` as NOT NULL and drop the `picture_ref` FKs and
columns from `GAS_CYLINDERS` and `SERVICE_PARTS`. There are no existing picture
rows, so no backfill or attribution is needed. On SQLite the NOT NULL add uses
`batch_alter_table`; on MSSQL the FKs are dropped before the columns.

Empty db => no need to migrate the data

## Risks / Trade-offs

- **[Spec overlap with the archived warehouse change]** `equipment` now carries
  the warehouse wording; this change's delta was rebased onto it (all five
  cylinder scenarios kept, `picture_ref` removed). → No archive-order dependency
  remains.
- **[Concurrent uploads from several tablets]** Two uploads can compute the same
  sequence. → Unique index on `path` plus retry on the insert.
- **[iPad HEIC]** A tablet may hand over HEIC, which browsers often cannot render
  in `<img>`. → The capture path usually yields JPEG; verify on the target
  device, and if HEIC appears, add client-side conversion or accept that only
  the download works. Tracked as a validation step, not a design change.
- **[Large photos]** 5–10 MB uploads. → nginx already allows 50 MB; client-side
  downscaling is a possible follow-up, out of scope here.

## Migration Plan

1. New Alembic revision (revises the current head, the refills/cylinder-archive
   revision): add `owner_type`/`owner_id` as NOT NULL and drop the `picture_ref`
   FKs and columns. No data migration — there are no picture rows.
2. `alembic upgrade head` on MSSQL; `flask dev-init`/`make dev-init` replays it
   for dev. Rollback re-adds the `picture_ref` columns and drops the owner
   columns.
3. Update `docs/openapi.yaml` (upload request, `Picture` schema, by-owner query,
   `RepairDetail.pictures`, removed `picture_ref`) and regenerate the frontend
   client.
4. Deploy backend first (upload contract and detail shape change), then the
   frontend.

## Open Questions

- None blocking. Thumbnail sizing/resizing and HEIC handling are deferred to
  implementation validation on the actual tablet.
