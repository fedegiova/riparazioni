# Design

## Context

See proposal.md for motivation. The relevant current state:

- Owned tables live in `app/models/owned.py` with UPPERCASE names and lowercase
  columns; migrations create only owned tables (`include_object` filter in
  `migrations/env.py`).
- `/api/v1` routes live in `app/routes/api/`, business rules in
  `app/services/`, and errors use the `{"error": "..."}` envelope
  (`app/routes/api/errors.py`). `docs/openapi.yaml` is the contract; the
  frontend client is generated from it (`npm run generate:api`).
- The React app renders feature screens inside `AppShell` (app bar + breadcrumb
  + bottom nav), with feature UI capabilities separate from backend ones
  (`repairs` vs `repairs-ui`).

## Goals / Non-Goals

**Goals:**
- One generic, durable settings store that any future setting can use.
- Store the three known settings with unambiguous, machine-readable values so
  later consumers (operator picker, work-log time calculation) can rely on them.
- Edit them from a single Settings page.

**Non-Goals:**
- Consuming the settings (no operator picker, no time calculation) — follow-up.
- Per-user settings, secrets, or settings that need typed columns.
- Holiday/working-hours semantics beyond storage: no overlap enforcement,
  time zones, or overnight shifts.

## Decisions

**Generic `name`/`value` table with JSON values.**
`SETTINGS(name VARCHAR(64) PK, value VARCHAR(4000))` where `value` holds a JSON
text document. Chosen over typed columns (a settings table with a column per
setting is not extensible) and over a text-only KV store (JSON removes encoding
ambiguity — the reason the format was chosen). `name` is the primary key so
`PUT /settings/<name>` is a natural upsert. `key` is avoided because MSSQL
reserves it.

**JSON-native API; the string is a storage detail.**
The API exchanges parsed JSON: `GET /api/v1/settings` returns a
name→value map; `GET/PUT/DELETE /api/v1/settings/<name>` read/replace/remove one
value; `PUT /api/v1/settings` updates several atomically. The frontend never
double-encodes. Alternative rejected: returning raw JSON strings and parsing in
the client, which leaks the storage detail into every caller.

**Validation dispatched by exact key, no key patterns.**
A registry in the settings service maps `operators`, `working_hours`, and
`holidays` to a validator; unknown names accept any JSON value. This is why
holidays are a single object keyed by year rather than `holidays.<year>` rows:
key-pattern matching in the write path was explicitly unwanted. Bulk writes
validate every provided known key first and commit nothing if any fails
(atomic).

**Known-key defaults synthesized on read, not seeded.**
`operators` → `[]`, `working_hours` → all days closed, `holidays` → `{}`. This
keeps migrations schema-only (a project rule) and gives the UI and future
consumers a complete view. Trade-off: "never configured" and "explicitly empty"
are indistinguishable; acceptable here.

**Encodings.**
- `operators`: `["MARIO", "LUIGI"]`.
- `working_hours`: `{"mon": [["08:00","12:00"],["14:00","18:00"]], ..., "sun": []}`;
  `HH:MM` 24h, begin strictly before end, `[]` = closed, missing day = closed.
- `holidays`: `{"2026": [{"from":"2026-01-01","to":"2026-01-01","name":"Capodanno"}]}`;
  four-digit year keys, ISO dates inside the mapped year, `from <= to`; a
  cross-year closure is two ranges. Year buckets are sparse.

**Frontend: gear in the app bar, dedicated page, capability split.**
The app bar gains a settings control next to the home control; `/settings`
renders the page inside the shell. The backend store/API is capability
`settings`; the page is capability `settings-ui`, mirroring the existing
`repairs`/`repairs-ui` split. Generated client types are free-form for setting
values, so the frontend keeps local TypeScript types for the three known shapes
plus parse/serialize helpers.

## Risks / Trade-offs

- [`value` VARCHAR(4000) could be too small as holidays grow] → holiday text is
  tiny per year; if it ever overflows, widen the column or split per year in a
  follow-up migration.
- [Free-form generated client types weaken type safety for setting values] →
  keep hand-written types and parse helpers for the three known settings, and
  validate server-side.
- [Synthesized defaults hide whether a setting was ever saved] → acceptable; the
  UI shows defaults, and future consumers get sane values.
- [A single JSON object for all holiday years rewrites every year on save] →
  fine at this scale; year buckets are small and writes are infrequent.

## Migration Plan

- One Alembic revision creates `SETTINGS`. No data migration and no seeding.
- Rollback: `downgrade` drops the table; the API then reports every known
  setting as its default, so nothing else depends on the table existing.
- Deploy order: apply the migration before serving the new frontend build
  (the page calls the new endpoints).

## Open Questions

- Whether the Settings page should also allow editing non-current holiday years
  via the selector, or only the current year plus years already stored. The
  selector design already supports either; no spec or task change is needed.
