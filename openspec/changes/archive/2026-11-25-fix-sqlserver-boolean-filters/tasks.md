# Tasks

## 1. Portable Boolean filters

- [x] 1.1 In `app/routes/api/equipment.py`, replace the Boolean `.is_(...)` comparisons in `list_gas_cylinders` (`GasCylinder.archived`) and `list_service_parts` (`ServicePart.is_refrigerator_part`) with `== db.false()` / `== db.true()`; verify `pytest tests/test_api_equipment.py` passes.
- [x] 1.2 Add a regression test in `tests/test_api_equipment.py` that compiles both list statements against the SQL Server dialect and asserts the Boolean filters render as `= 0`/`= 1` and never as `IS 0`/`IS 1`; verify the test fails when a `.is_(...)` comparison is restored and passes with the fix.

## 2. Integration verification

- [x] 2.1 Run `pytest` and confirm the equipment tests and the new dialect-compilation test pass with no new regressions.
- [x] 2.2 On a SQL Server instance, GET `/api/v1/gas-cylinders` and `/api/v1/service-parts?is_refrigerator_part=true` and confirm both return HTTP 200 instead of the `Incorrect syntax near '0'` error.
