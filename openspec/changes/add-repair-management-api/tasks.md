# Tasks

## 1. Database models and migration

- [x] 1.1 Create owned models (`Repairs`, `RepairWorkLog`, `RepairPart`, `Refrigerator`, `GasCylinder`, `ServicePart`, `Picture`) in `app/models/` with the normalized columns and relationships from design.md, re-exported in `app/models/__init__.py` — verify: a test asserting the SQLAlchemy registry contains all seven mapped classes passes
- [x] 1.2 Create read-only external models (`Vehicle` → TBALLESTIMENTI, `Customer` → VICLIENTI view, `AppUser` → TBUSERS) as `Table`-based mapped classes in schema `DATIDBSTORICO` — verify: a test asserting table names, schema, and mapped columns passes
- [x] 1.3 Add a pytest DB fixture: creates owned + external tables on in-memory SQLite, rewrites the `DATIDBSTORICO.` prefix, enables `PRAGMA foreign_keys`, and seeds vehicle/customer reference rows — verify: a fixture sanity test inserting a repair whose FKs point at the seeded external rows passes
- [x] 1.4 Generate the initial Alembic migration creating the seven owned tables (none in `DATIDBSTORICO`) — verify: `flask db upgrade` and `flask db downgrade -1` both succeed against the test SQLite database (test)
- [ ] 1.5 Smoke-check the external tables against a live MSSQL database (column names of TBALLESTIMENTI, VICLIENTI, TBUSERS) and fix any model mismatch — verify: a documented query against the real DB returns rows and matches the mapped columns

## 2. Reference data API (read-only)

- [x] 2.1 Implement `/api/v1/vehicles` list + detail endpoints; writes rejected with 405 — verify: API tests for list, detail, unknown ID (404), and POST (405) pass
- [x] 2.2 Implement `/api/v1/customers` list + detail endpoints — verify: API tests for list, detail, and unknown ID (404) pass
- [x] 2.3 Implement `/api/v1/users` list + detail endpoints excluding the password field — verify: a test asserting the response JSON has no password key passes

## 3. Equipment API (CRUD)

- [x] 3.1 Implement `/api/v1/refrigerators` CRUD — verify: API tests for create (201), list, detail, update, delete (204), delete-while-referenced (409), and unknown ID (404) pass
- [x] 3.2 Implement `/api/v1/gas-cylinders` CRUD with remaining weight defaulting to full weight on create — verify: API tests for create (including the default-remaining-weight scenario), list, detail, update, delete, delete-while-referenced (409), and unknown ID (404) pass
- [x] 3.3 Implement `/api/v1/service-parts` CRUD with the `is_refrigerator_part` list filter — verify: API tests for create, list (with and without filter), detail, update, delete-while-referenced (409), and unknown ID (404) pass

## 4. Pictures API and file storage

- [x] 4.1 Implement the picture storage service (unique `<uuid-hex><ext>` name under `UPLOAD_DIR/pictures`, relative path stored in metadata, file removal on delete) — verify: unit tests for name uniqueness, extension preservation, and file removal on delete pass
- [x] 4.2 Implement `/api/v1/pictures` endpoints: multipart upload, list, detail, file download, delete — verify: API tests for upload (201 + file on disk), missing file (400), download (200 with matching content type), missing file on disk (404), delete-while-referenced (409), and delete (204 + file gone) pass

## 5. Repairs API

- [x] 5.1 Add JSON error handlers for the `api` blueprint (400/404/405/409 with the `{"error": ...}` envelope, 409 from `SQLAlchemyIntegrityError`) — verify: tests hitting an unknown resource and an FK-violating write return the envelope with the correct status code
- [x] 5.2 Implement `/api/v1/repairs` CRUD: create (type validation, default start datetime), list with customer/vehicle/refrigerator/type/date filters, detail including work log and parts, update (complete/reopen via end datetime), delete with cascade — verify: API tests covering every scenario in the repairs spec pass
- [x] 5.3 Implement parts association on repair create/update (quantity + optional unit price) — verify: API tests for create-with-parts, unknown part (409), and parts present in detail pass
- [x] 5.4 Implement nested `/api/v1/repairs/<id>/work-log` CRUD — verify: API tests for add (201), entry visible in repair detail, update, delete (204), and unknown repair (404) pass
- [x] 5.5 Implement gas recharge handling in the service layer: cylinder + weight required, state validation per repair type, balance decrease in the same transaction, overdraw rejected (400), balance restored when a recharge entry is deleted — verify: API tests for every gas-recharge scenario in the repairs spec (VUOTO balance math, PIENO, RICUPERO_RICARICA, overdraw, missing cylinder, restore-on-delete) pass

## 6. Integration and documentation

- [x] 6.1 Add an end-to-end API test: create RIPA_FRIGO repair → work-log entry with recharge → assert cylinder balance → add a part → complete the repair → list filtered by customer — verify: the integration test passes
- [x] 6.2 Document all new endpoints in README.md and add a manual MSSQL smoke checklist (run `flask db upgrade` against the real DB, verify the external tables, curl one endpoint per group) — verify: the README sections exist and every documented command is written exactly as it should be run
- [x] 6.3 Run the full verification suite — verify: `ruff check .` and `pytest` both pass
