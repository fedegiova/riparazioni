# Design

## Context

See proposal.md for motivation. Current state that shapes the approach:

- The app is a Flask application factory (`create_app` in `app/__init__.py`)
  whose database settings are read from the environment at config-class
  evaluation time (`app/config.py`); `DATABASE_URL` defaults to a local MSSQL
  connection. `tests/conftest.py` overrides `SQLALCHEMY_DATABASE_URI` and
  engine options on the created app — the established pattern for pointing
  the app at a different database.
- The read-only legacy objects live in the `DATIDBSTORICO` schema
  (`app/models/external.py` maps them on the app's SQLAlchemy metadata with
  `schema="DATIDBSTORICO"`). Migrations must never create or alter them —
  the `include_object` filter in `migrations/env.py` excludes that schema,
  and `tests/test_migration.py` asserts it.
- The test suite already fakes the legacy schema on SQLite:
  `ATTACH DATABASE ':memory:' AS DATIDBSTORICO` on a connect event listener,
  `metadata.create_all` for the external tables, and hand-seeded rows. This
  is proven machinery this change reuses for file-backed databases.
- `tests/test_migration.py` shows the proven way to run Alembic
  programmatically in an app context: `Config("migrations/alembic.ini")` +
  `script_location` + `command.upgrade/downgrade`.
- `clienti.sql` at the repo root is the MSSQL-dialect sample dump (3-part
  names, `GO` separators, `{d '...'}` date literals, CHAR padding) that the
  prebaked seed is derived from.
- `Makefile` targets set environment variables inline (`FLASK_DEBUG=1
  $(FLASK) run`); `var/` is the gitignored runtime directory
  (`var/uploads`, `var/log`).

Constraints: no API/contract changes, no production or testing changes, no
new runtime dependencies, migrations stay owned-tables-only.

## Goals / Non-Goals

**Goals:**

- `DEV_MODE=1` makes the development app run entirely on local SQLite files
  (no MSSQL, no ODBC driver).
- An explicit, idempotent `flask dev-init` command prepares the dev
  databases (migrations + external tables + seed); `--reset` wipes and
  re-prepares. `make dev` = init + server, the one-command dev story.
- Prebaked external reference data (customer, vehicle, user) derived from
  `clienti.sql`, committed as an editable file and replaceable wholesale via
  configuration.
- The existing test suite keeps passing untouched; new behavior is covered
  by new tests.

**Non-Goals:**

- No auto-initialization at app startup (user decision: setup is explicit;
  the app factory only configures the engine, never runs DDL).
- No seeding of owned tables — refrigerators, cylinders, parts, and repairs
  start empty and are created through the API.
- No reset of `var/uploads` picture files on `--reset` (the directory is
  shared with the MSSQL-based dev flow).
- No dev-mode support for the `testing` or `production` configs, no Docker,
  no changes to the frontend dev workflow (it already proxies to
  `127.0.0.1:5000`, where `make dev` listens).

## Decisions

### 1. Dev mode is a config flag on `DevelopmentConfig` only

`DEV_MODE = _bool("DEV_MODE", False)` is defined on `DevelopmentConfig`
alone, following the existing `_env`/`_bool` env-reading helpers. The
factory checks the *final* `app.config` value (tests inject a config
subclass with the flag via `app.CONFIGS`) and, when true, applies dev-mode
wiring (decision 2) around `db.init_app`. `TestingConfig` and
`ProductionConfig` never define the flag, so they are unaffected even if
`DEV_MODE` is set in the environment.

Implementation note (verified against the installed Flask-SQLAlchemy 3.x):
`db.init_app` creates the engine **eagerly** from the config at that
moment, so the URI swap must run *before* `db.init_app`, not after. Dev
wiring is therefore two-phase: `setup_dev_mode(app)` (config only) before
`init_app`, `install_dev_engine_hooks(app)` (connect listener on the
already-created engine) after.

In dev mode the database URL is resolved as
`DEV_DATABASE_URL` (full `sqlite:` URL) or, when unset, the default
`sqlite:///<BASE_DIR>/var/dev.sqlite3`. An explicitly set `DATABASE_URL` is
**ignored** while dev mode is active — dev mode means "local SQLite", and
the override that matters is `DEV_DATABASE_URL`. This is documented in
`.env.example` and the README.

*Alternatives considered:* a new `FLASK_ENV` value (rejected — changes the
config matrix and the `wsgi.py`/systemd contract); implicit dev mode for
`FLASK_ENV=development` (rejected — silently re-points existing local MSSQL
developers, user chose explicit opt-in); `DATABASE_URL`-based detection
(rejected — the default is already a non-empty MSSQL URL, so "was it set
explicitly" is indistinguishable).

### 2. Two SQLite files; external file `ATTACH`ed as `DATIDBSTORICO`

The ORM maps the external tables with `schema="DATIDBSTORICO"`, so queries
render `DATIDBSTORICO.TBALLESTIMENTI` and friends. SQLite resolves a schema
qualifier to an attached database, so the external tables live in a second
file attached at connect time — exactly the conftest pattern, but
file-backed:

- primary: `var/dev.sqlite3` (owned tables, Alembic-managed)
- external: `var/dev_external.sqlite3` (the three legacy tables)

A new module `app/dev_db.py` owns all dev-mode logic:

- `setup_dev_mode(app)` — phase 1, called by the factory *before*
  `db.init_app` (the engine is created there, eagerly): sets
  `SQLALCHEMY_DATABASE_URI` to the resolved dev URL,
  `SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread":
  False}}` (the Flask dev server is multithreaded; conftest uses the same
  option), and records the resolved paths in config
  (`DEV_DATABASE_PATH` / `DEV_EXTERNAL_DATABASE_PATH`) for `init_dev_app`.
- `install_dev_engine_hooks(app)` — phase 2, called by the factory *after*
  `db.init_app`: registers a `connect` event listener on `db.engine` that
  runs `ATTACH DATABASE '<external path>' AS DATIDBSTORICO` and
  `PRAGMA foreign_keys=ON` on every new DBAPI connection (FK enforcement
  for parity with production; the pragma is per-connection, so it must ride
  on the listener). The attach path is embedded in the SQL literal with
  single quotes doubled (ATTACH takes no bound parameters). Listener
  installation is idempotent (guarded by a per-engine marker) so calling it
  twice on one engine cannot double-attach.
- `init_dev_app(app, reset=False, seed_path=None)` — the initialization
  logic (decision 3), importable from tests without invoking the CLI.
- The external file's location resolves as `DEV_EXTERNAL_DATABASE_URL` (full
  `sqlite:` URL), or when unset, by deriving the sibling of the primary file
  with an `_external` suffix (`dev.sqlite3` → `dev_external.sqlite3`).

*Alternatives considered:* a single file with unqualified table names (would
require rewriting the models' schema or per-dialect table naming — more
invasive than attaching, and breaks the "identical queries" property the
tests rely on); attaching `:memory:` like the tests (no — dev data must
persist across server restarts).

### 3. `flask dev-init`: explicit, idempotent, alembic-driven

A Click command `dev-init` (registered on `app.cli`) with `--reset` and
`--seed PATH` options wraps `init_dev_app`. It is the only code path that
runs DDL; the app factory and request handling never do.

Seed source resolution order: `--seed` flag → `DEV_SEED_SQL` env var → the
committed `dev/seed_external.sql`. A missing/unreadable seed file is a hard
error with the path named.

Plain run (idempotent):

1. Ensure the parent directories of both files exist.
2. Owned tables: `alembic command.upgrade(cfg, "head")` with
   `Config("migrations/alembic.ini")` + `script_location`
   (`migrations/`), run inside the app context — the same proven pattern as
   `tests/test_migration.py`. The `include_object` filter keeps this
   owned-tables-only; external DDL never flows through Alembic.
3. External tables: `db.metadata.create_all(engine, tables=[the three
   external Table objects], checkfirst=True)` — the DDL renders as
   `CREATE TABLE "DATIDBSTORICO".<name>` against the attached file and stays
   in sync with `app/models/external.py` automatically.
4. Seed: if **all three** external tables are empty, execute the seed file's
   statements via `executescript` on the engine connection (the attach
   listener already covers it). "All three empty" is the freshness test: a
   partially populated dev database is left alone, and reseeding always
   goes through `--reset`.

`--reset` run: `alembic command.downgrade(cfg, "base")` (drops the seven
owned tables; safe on SQLite — the migration's downgrade order is
FK-correct), then the plain run above with the external tables first
`DROP TABLE IF EXISTS "DATIDBSTORICO".<name>`-ed so create+seed happen
unconditionally. Owned tables end up empty at head; external tables contain
exactly the active seed rows. Uploaded picture files are intentionally not
touched (non-goal).

The command prints a short summary (resolved paths, what was migrated,
seeded, or skipped) so `make dev` output is self-explanatory.

*Alternatives considered:* auto-migrate at startup (rejected by user
decision — startup DDL would surprise and would couple server boot to
migration state); `db.metadata.create_all` for owned tables instead of
Alembic (rejected — dev would then never exercise the real migration
path, defeating a key purpose of a local dev database); a separate
`flask dev-migrate` + `flask dev-seed` pair (rejected — one command, one
mental model; the Makefile stays two lines).

### 4. Prebaked seed file: committed, SQLite-dialect, INSERT-only

`dev/seed_external.sql` is hand-derived once from `clienti.sql` and
committed: same rows (one customer "PP.", one IVECO vehicle, one user
"LORENZA"), adapted to SQLite — 3-part names reduced to
`DATIDBSTORICO.<table>`, `GO` removed, `{d '2003-09-01'}` written as ISO
`'2003-09-01'`, trailing CHAR padding stripped and whitespace-only values
written as `NULL`. `ID`/`N_NOMINATIVO` on the customer row are plain
integers (the models map them as `Integer`, and the API validates repair
references as integers); `ID_INT` values are kept from the sample so seeded
repairs reference recognizable ids (customer 9, vehicle 12363, user 21).
The file header documents its provenance and that `DEV_SEED_SQL`/`--seed`
can replace it. The file contains INSERTs only — DDL is always generated
from the models, so the dev schema cannot drift from `app/models/external.py`.

*Alternatives considered:* parsing `clienti.sql` (T-SQL) at runtime
(rejected — `GO` batches and `{d}` literals make it fragile for no benefit);
seeding from a Python module in `app/` (rejected — developers should be able
to edit data without touching Python, and the SQL file is diff- and
gitleaks-reviewable in its raw form).

### 5. Makefile and documentation

```make
dev-init:
	DEV_MODE=1 $(BIN)/flask dev-init

dev:
	DEV_MODE=1 $(BIN)/flask dev-init
	DEV_MODE=1 FLASK_DEBUG=1 $(FLASK) run
```

matching the existing inline-env-var target style. `.env.example` gains the
documented block (`DEV_MODE` default off, `DEV_DATABASE_URL`,
`DEV_EXTERNAL_DATABASE_URL`, `DEV_SEED_SQL` — all commented out with the
defaults). README gains a "Development without MSSQL (dev mode)" section:
`make dev`, `flask dev-init --reset`, how to customize the seed (edit the
file or point `DEV_SEED_SQL` at your own, then reset), what the prebaked
data contains, and that production/testing are unaffected.

### 6. Tests: `tests/test_dev_mode.py`

A test helper builds the app with `create_app("development")` after patching
a dev-mode config class (tmp `BASE_DIR`, `DEV_DATABASE_URL`,
`DEV_EXTERNAL_DATABASE_URL`) into `app.CONFIGS` — the config module reads
the environment at import time, so the class level is the injection point;
the factory then performs the full dev wiring. `init_dev_app(app, ...)` is
called explicitly inside the app context:

- Config resolution: dev mode off keeps the MSSQL default; `DEV_MODE` on
  resolves the tmp sqlite URL; `DEV_DATABASE_URL`/`DEV_EXTERNAL_DATABASE_URL`
  overrides honored; `production` config ignores `DEV_MODE`.
- Init: after `init_dev_app`, `alembic_version` is at head, the seven owned
  tables exist, the three external tables exist under the
  `DATIDBSTORICO` schema (inspector), and the seeded rows are present
  (ORM counts + spot values: vehicle `ID_INT=12363`, customer `ID=9`,
  user `ID_INT=21`, no password exposed).
- Idempotency: a second init leaves API-created rows intact and adds no
  duplicate seed rows.
- Reset: owned tables empty at head, external tables exactly the seed rows;
  reset on a fresh environment just initializes.
- Custom seed: a temp SQL file (e.g. two customers) via `seed_path` +
  `init_dev_app(reset=True)` replaces the prebaked rows.
- End-to-end on the dev app: `/healthz/db` 200; `GET /api/v1/vehicles`,
  `/customers`, `/users` return the seeded rows with production shapes;
  `POST /api/v1/repairs` with seeded `customer=9, vehicle=12363` → 201;
  with an unknown customer → 409; write to a reference endpoint → 405;
  deleting a referenced refrigerator → 409 (FK enforcement active).

## Risks / Trade-offs

- [SQLite file locking under the Flask dev server (reloader = 2 processes)]
  → both processes attach the same files; SQLite handles concurrent
  read/write with its file locks — short writer blocking is acceptable for
  single-developer use. No WAL (unnecessary at this scale).
- [Per-connection `ATTACH` + pragma cost] → negligible (two statements per
  new DBAPI connection; pooled connections keep the attach).
- [Listener double-registration if `setup_dev_mode` runs twice on one
  engine] → guarded by a per-engine marker; tests may call it repeatedly on
  the same app safely.
- [Seed values diverge from real legacy data] → they are a sample; the
  stripping/padding normalization is documented in the file header, and the
  whole point of `DEV_SEED_SQL` is to replace them.
- [Reset orphans picture files in `var/uploads`] → known, documented
  non-goal (the directory is shared with the MSSQL dev flow, so wiping it
  from a SQLite reset would be worse).
- [`DEV_MODE` set with a non-default `FLASK_ENV`] → only `DevelopmentConfig`
  defines the flag; other environments are unaffected by construction,
  covered by a test.
- [Conftest/dev_db pattern duplication] → the 4-line attach listener pattern
  exists in two places (tests must stay independent of app dev-mode code);
  accepted over extracting a shared helper the test suite would import.

## Migration Plan

Pure addition to the codebase; nothing existing changes behavior:

- Deploy = merge. `make run` (MSSQL flow), `make test`, and production are
  untouched — dev mode is inert without `DEV_MODE=1`.
- Rollback = revert the commit; dev SQLite files live in gitignored `var/`
  and can be deleted. No data migration, no production migration.
- Existing developers who use local MSSQL keep their exact workflow; new
  developers can use `make dev` instead of the ODBC/MSSQL setup.

## Open Questions

None — the two scope-affecting choices (explicit opt-in switch; explicit
setup step rather than startup auto-init) were resolved with the user
during planning.
