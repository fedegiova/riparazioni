# Tasks

## 1. Settings model and migration

- [x] 1.1 Add a `Settings` owned model (`name` string primary key, `value` string) in `app/models/owned.py` with a `to_dict`, and export it from `app/models/__init__.py`; verify `import app.models` succeeds and `flask db migrate` detects the new table
- [x] 1.2 Create the Alembic revision that adds `SETTINGS`; verify the migration round-trip test (`tests/test_migration.py`) passes upgrade and downgrade

## 2. Settings service and API

- [x] 2.1 Add a settings service providing the known-key defaults and validators for `operators`, `working_hours`, and `holidays` (unknown names accept any JSON); verify unit tests cover each valid shape and each rejected shape
- [x] 2.2 Add the settings route module (`GET /api/v1/settings`, `GET/PUT/DELETE /api/v1/settings/<name>`, `PUT /api/v1/settings`) and register it on the `/api/v1` blueprint; verify endpoint tests pass, including upsert, defaults on read, 404 for unknown, and the 400 error envelope
- [x] 2.3 Make the bulk `PUT /api/v1/settings` atomic and validated before commit; verify a test that mixes one invalid known value with valid ones leaves every stored setting unchanged

## 3. API contract and documentation

- [x] 3.1 Add the settings paths and schemas to `docs/openapi.yaml`; verify the document still validates and `npm run generate:api` regenerates without error
- [x] 3.2 Regenerate and commit the frontend client (`frontend/src/api/generated/schema.d.ts`); verify the frontend type-check (`npm run build`) passes against it
- [x] 3.3 Document the settings endpoints in the README API section; verify the documented methods and paths match the implemented routes

## 4. Frontend settings page and shell

- [x] 4.1 Add a settings API module plus local TypeScript types and parse/serialize helpers for the three known settings; verify frontend tests cover parsing and serializing each shape
- [x] 4.2 Build the Settings page editors — operators list, per-weekday working hours, and holidays with a year selector — with load, save, and error display; verify page tests cover load, save, a rejected save, and each editor
- [x] 4.3 Add the app-bar settings control, the `/settings` route, and the settings breadcrumb in `AppShell`; verify shell/route tests cover opening settings from the control and rendering the route directly

## 5. Integration verification

- [x] 5.1 Run the full backend suite (`make test`) and lint (`make lint`), then exercise the flow in dev mode (`make dev`): edit and save all three settings, reload the page, and confirm the values persist
