# Design

## Context

See proposal.md — Why. Relevant current state:

- `app/models/external.py` maps the pre-existing objects with
  `db.Table(..., schema="DATIDBSTORICO")` (hard-coded). Alembic's
  `include_object` in `migrations/env.py` excludes `type_ == 'table'` with
  `schema == 'DATIDBSTORICO'`.
- Dev mode (`app/dev_db.py`) `ATTACH`es a separate SQLite file
  `AS DATIDBSTORICO` and seeds it with `dev/seed_external.sql`, whose
  statements are written `DATIDBSTORICO.<table>`.
- The test suite (`tests/conftest.py`) attaches an in-memory database
  `AS DATIDBSTORICO`; `tests/test_models.py` asserts the schema is
  `DATIDBSTORICO`.
- `app/__init__.py` calls `load_dotenv()` before importing `app.config`, so a
  module-level setting in `app/config.py` sees the environment.

## Goals / Non-Goals

**Goals:**

- Make the single legacy-object qualifier configurable, so SQL Server can use
  the cross-database `AHR_GIOPLAST.DATIDBSTORICO` name.
- Keep one source of truth for that name across models, migrations, and dev
  mode.
- Preserve dev mode and the SQLite test suite unchanged under the default.

**Non-Goals:**

- Changing the API contract, response shapes, or the OpenAPI document.
- Changing owned tables or adding an Alembic migration.
- Supporting a cross-database qualifier inside SQLite dev mode.

## Decisions

**One `EXTERNAL_DB_SCHEMA` setting, default `DATIDBSTORICO`.**
Defined once in `app/config.py` (module constant plus a `BaseConfig`
attribute) and consumed by the external mappings, the migration filter, and
dev mode. Alternatives considered: hard-coding `AHR_GIOPLAST.DATIDBSTORICO`
(would break the SQLite `ATTACH`, the committed seed SQL, and the specs, all
of which name `DATIDBSTORICO`); deriving the prefix from `DATABASE_URL`
(fragile, and the URL does not carry the external database name).

**Let SQLAlchemy expand the dotted schema; no dialect branches.**
A `schema` string containing dots compiles to `[AHR_GIOPLAST].[DATIDBSTORICO].
[<table>]` on the MSSQL dialect and to `"AHR_GIOPLAST.DATIDBSTORICO".
[<table>]` on SQLite (a single quoted identifier). Verified against both
dialects, so production needs no special-casing and dev/tests keep working.

**Read the setting at import; document the ordering.**
`Table` schemas are fixed when the models are defined, so the constant is read
at import time, after `load_dotenv()`. A `_table` helper accepts an explicit
`schema` argument (defaulting to the constant) so tests can exercise the
3-part rendering without changing the process environment.

**Filter migrations by the configured qualifier.**
`include_object` compares against `EXTERNAL_DB_SCHEMA` instead of the literal
`DATIDBSTORICO`, so the external objects stay excluded from autogenerate and
`db upgrade` once production uses the 3-part name.

**Reject a cross-database qualifier in dev mode.**
SQLite attaches one file under one schema name and the prebaked seed targets
it unqualified, so `setup_dev_mode` raises a clear error when the configured
qualifier contains a dot. Alternatives considered: rewriting the seed's
`DATIDBSTORICO.` prefix at run time (extra complexity for a case no developer
needs).

## Risks / Trade-offs

- [A developer sets `EXTERNAL_DB_SCHEMA` to the 3-part name and breaks dev
  startup] → `setup_dev_mode` fails fast naming the setting and the required
  bare name.
- [Reading the setting at import makes per-test overrides awkward] → Tests keep
  the default; the regression test passes an explicit `schema` to `_table`.
- [Alembic may report the schema differently than configured] → The external
  objects live in another database and are not reflected in the connected
  database anyway; the filter is a guard, not the only exclusion.

## Migration Plan

Configuration-only change; no schema or data migration. On the SQL Server
deployment set `EXTERNAL_DB_SCHEMA=AHR_GIOPLAST.DATIDBSTORICO` in the service
environment and restart. Rollback is unsetting the variable. Dev mode and the
test suite need no change.

## Open Questions

None.
