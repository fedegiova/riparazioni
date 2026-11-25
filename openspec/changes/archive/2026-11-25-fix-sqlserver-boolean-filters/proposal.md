# Proposal

## Why

Boolean filters on the equipment endpoints fail against SQL Server in
production. SQLAlchemy compiles `.is_(False)` / `.is_(True)` on a `Boolean`
column to `IS 0` / `IS 1`, and SQL Server rejects that syntax for `BIT` columns
(`Incorrect syntax near '0'`, error 102), so `GET /api/v1/gas-cylinders` and
`GET /api/v1/service-parts?is_refrigerator_part=...` return HTTP 500. SQLite
accepts `IS 0`, which is why the SQLite-only test suite never caught it.

## What Changes

- In `app/routes/api/equipment.py`, compare Boolean columns with
  `db.true()` / `db.false()` instead of `.is_(...)`, so the query compiles to
  `= 1` / `= 0` on every dialect (including SQL Server) while keeping the same
  filter semantics.
- Leave the existing `IS NULL` comparisons (`RepairWorkLog.end_time.is_(None)`,
  `Repairs.end_data.is_(None)`) unchanged: `IS NULL` is portable.
- Add regression coverage that guards against regenerating `IS <literal>` for
  Boolean columns on the SQL Server dialect.

## Capabilities

### New Capabilities
<!-- None: the change restores behavior the existing equipment requirements already promise. -->

### Modified Capabilities
- `equipment`: the archived-cylinder filter and the service-part
  `is_refrigerator_part` filter must work on both supported databases
  (SQLite and SQL Server), not just SQLite.

## Impact

- Backend: `app/routes/api/equipment.py` (`list_gas_cylinders`,
  `list_service_parts`); `tests/test_api_equipment.py` (new regression case).
- API contract: unchanged; no `docs/openapi.yaml` or generated-client change.
- Database support: the change is what makes the equipment filters usable on
  SQL Server, matching the existing SQLite behavior.
