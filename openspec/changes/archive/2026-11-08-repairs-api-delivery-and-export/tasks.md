# Tasks

## 1. Schema and migration

- [x] 1.1 Add nullable `delivery_date` (Date) to the `Repairs` model and remove the `type` column; verify the app imports and `make lint` passes
- [x] 1.2 Autogenerate the Alembic revision dropping `REPAIRS.type` and adding `REPAIRS.delivery_date`, and verify `make db-upgrade` applies it and the downgrade restores the prior shape
- [x] 1.3 Update the migration round-trip test for the new schema and verify `tests/test_migration.py` passes

## 2. Repairs API: remove `type`, add `delivery_date`, generalize the gas rule

- [x] 2.1 Remove `type` from the repair create/update/list/detail paths and payloads, add `delivery_date`, and verify the repairs API tests cover the new shape and pass
- [x] 2.2 Generalize the gas rule so any gas-carrying work-log entry requires `gas_system_state`, and verify the gas tests pass including a new "gas data without a state is rejected" case
- [x] 2.3 Update `docs/openapi.yaml` to drop `type`, add `delivery_date`, and adjust the gas-rule description, and verify it matches the running app

## 3. Computed list/detail fields

- [x] 3.1 Compute `total_hours` as the sum of work-log durations in the list and detail responses, and verify a test asserting 1h30 + 2h00 -> 3h30 and that null-duration entries contribute zero
- [x] 3.2 Resolve and include `customer_name` from the reference data for list and detail, and verify tests against the DATIDBSTORICO shim including a customer id with no matching record
- [x] 3.3 Reflect `total_hours` and `customer_name` in `docs/openapi.yaml`, and verify the documented response shape matches the app

## 4. Excel export

- [x] 4.1 Add `openpyxl` to `requirements.txt` and install it, and verify the import succeeds in the virtualenv
- [x] 4.2 Add `GET /api/v1/repairs/export` reusing the list filters and writing an .xlsx workbook, and verify an API test downloads it with one row per matching repair
- [x] 4.3 Document the export endpoint in `docs/openapi.yaml` and verify it lists the correct Excel content type

## 5. Integration

- [x] 5.1 Run `make lint` and `make test` and verify the full suite passes with `docs/openapi.yaml` validated against the running app
