# Proposal

## Why

The application has no place to keep workshop-wide configuration. Two values
are needed now and will be consumed by follow-up work: the list of operators
and the factory working hours (later used to subtract non-working time from
work-log duration calculations), plus the yearly holiday calendar. Today
these live nowhere — the work-log operator is free text and no working-hours
data exists. A generic settings store gives the workshop a place to maintain
this data from the UI.

## What Changes

- Add an owned `SETTINGS` table storing `name`/`value` string pairs, where the
  value holds a JSON document.
- Add `/api/v1` endpoints to read, upsert, and delete settings, with the API
  exchanging parsed JSON values (the string encoding is a storage detail).
- Validate the known settings at write time: `operators` (array of strings),
  `working_hours` (per-weekday list of `HH:MM` intervals), and `holidays`
  (per-year list of named date ranges). Unknown keys accept any valid JSON.
- Add a Settings page at `/settings`, reached from a gear control in the app
  bar, with editors for operators, working hours, and holidays (year selector).
- Keep `docs/openapi.yaml` and the generated frontend client in sync.

No consumers are wired in this change: the operators list, working hours, and
holidays are stored and editable only. Using them (e.g. operator picker,
work-log time calculation) is follow-up work.

## Capabilities

### New Capabilities

- `settings`: an application settings store (owned table + JSON-native API)
  with validated known keys for operators, working hours, and holidays.
- `settings-ui`: the Settings page editors for operators, working hours, and
  holidays, reached from the app shell.

### Modified Capabilities

- `frontend-app`: the app shell gains a settings control and the `/settings`
  route.

## Impact

- **Backend**: new owned model `Settings`, a migration, a `settings` API route
  module, a settings service with per-key validators, and registration of the
  route module on the `/api/v1` blueprint.
- **Contract**: `docs/openapi.yaml` gains the settings paths and schemas; the
  frontend client is regenerated from it.
- **Frontend**: new `SettingsPage`, a `settings` API module, an app-bar gear
  control, a `/settings` route, and breadcrumb/nav wiring in `AppShell`.
- **Tests**: backend endpoint/validation tests and frontend page tests.
- No change to the external `DATIDBSTORICO` schema, and no change to existing
  endpoints.
