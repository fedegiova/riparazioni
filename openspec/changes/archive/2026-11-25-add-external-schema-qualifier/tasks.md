# Tasks

## 1. Configurable schema qualifier

- [x] 1.1 Add `EXTERNAL_DB_SCHEMA` (module constant plus `BaseConfig` attribute) in `app/config.py`; verify `python -c "from app.config import EXTERNAL_DB_SCHEMA; print(EXTERNAL_DB_SCHEMA)"` prints `DATIDBSTORICO`.
- [x] 1.2 Address the external mappings through that qualifier in `app/models/external.py` (the `_table` helper defaults to it and accepts an explicit `schema`); verify `pytest tests/test_models.py` passes.
- [x] 1.3 Compare the Alembic external-object exclusion in `migrations/env.py` against the configured qualifier instead of the literal; verify `pytest tests/test_migration.py` passes.
- [x] 1.4 Add a regression test in `tests/test_models.py` asserting MSSQL compiles `[AHR_GIOPLAST].[DATIDBSTORICO].[TBALLESTIMENTI]` for a dotted schema; verify the test fails if the 3-part expansion is removed.

## 2. Dev mode and documentation

- [x] 2.1 In `app/dev_db.py`, route the SQLite `ATTACH` and external DDL through the configured qualifier and raise a clear error when it is a cross-database 3-part name; verify `pytest tests/test_dev_mode.py` passes and that starting dev mode with `EXTERNAL_DB_SCHEMA=AHR_GIOPLAST.DATIDBSTORICO` fails with the named error.
- [x] 2.2 Document `EXTERNAL_DB_SCHEMA` in `.env.example` and the `README.md` configuration table; verify the documented name and default match `app/config.py`.

## 3. Integration verification

- [x] 3.1 Run the full `pytest` suite and confirm no regressions.
- [x] 3.2 On a SQL Server instance with `EXTERNAL_DB_SCHEMA=AHR_GIOPLAST.DATIDBSTORICO`, GET `/api/v1/vehicles`, `/api/v1/customers`, and `/api/v1/users` and confirm all return HTTP 200 instead of a resolution error.
