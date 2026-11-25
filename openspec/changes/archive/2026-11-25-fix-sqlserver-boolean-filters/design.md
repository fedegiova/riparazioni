# Design

## Context

See proposal.md — Why. Relevant current state:

- `app/routes/api/equipment.py` filters Boolean columns with `.is_(...)`:
  `GasCylinder.archived.is_(False)` in `list_gas_cylinders` and
  `ServicePart.is_refrigerator_part.is_(flag)` in `list_service_parts`.
- SQLAlchemy renders `.is_(False)`/`.is_(True)` on a `Boolean` column as
  `IS 0`/`IS 1` on the MSSQL dialect. SQL Server rejects that for `BIT`
  columns; SQLite accepts it.
- `db` (Flask-SQLAlchemy) exposes `db.true()`/`db.false()` constructs.
- The suite runs on in-memory SQLite (`tests/conftest.py`); there is no SQL
  Server in CI, so the failure is invisible to the current tests.

## Goals / Non-Goals

**Goals:**

- Make the archived-cylinder and service-part flag filters work on both
  supported databases.
- Add a regression test that fails if a Boolean filter regresses to
  `IS <literal>` compilation.

**Non-Goals:**

- Changing any `IS NULL` comparison: `.is_(None)` is portable and correct.
- Adding a live SQL Server to the test suite or CI.
- Changing the API contract, response shapes, or the OpenAPI document.

## Decisions

**Compare Boolean columns with `db.true()` / `db.false()`.**
`column == db.false()` compiles to `= 0` and `column == db.true()` to `= 1` on
every dialect. Alternatives considered: `== True` / `== False` (same SQL, but
ruff E712 flags it), and `.is_(db.false())` (still compiles to `IS 0`). For
`list_service_parts` the parsed flag selects `db.true()` or `db.false()`, so
both filter values stay portable.

**Guard portability with a dialect-compilation test.**
The SQLite test database cannot reproduce the failure, and there is no live
SQL Server in the suite. The regression test compiles the two list statements
against the SQL Server dialect and asserts the SQL contains `= 0`/`= 1` and no
`IS 0`/`IS 1`. Asserting on the absence of the invalid form (rather than an
exact SQL string) keeps the test stable across SQLAlchemy/SQL Server versions.
The test builds the same filter conditions the routes build; if the routes
change shape, the test is updated alongside.

## Risks / Trade-offs

- [Another Boolean `.is_(...)` exists elsewhere and regresses later] → A grep
  confirms only these two call sites; the new test covers them, and the
  `.is_(None)` calls are deliberately out of scope.
- [SQLAlchemy changes how it renders the Boolean comparison] → The test
  asserts "no `IS <literal>`", not an exact string, so a reasonable rendering
  change does not break it.
- [A contributor reintroduces `.is_(False)` in a new route] → The test covers
  only the existing queries; preventing this broadly would need a lint rule,
  which is out of scope for this fix.

## Migration Plan

Code-only change; no schema or API change, so no Alembic migration. Deploy the
updated backend and restart the service (gunicorn). Rollback is reverting the
commit.
