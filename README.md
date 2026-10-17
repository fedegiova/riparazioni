# riparazioni

Flask web application for managing repairs. It runs on a Linux server,
writes to the local filesystem (uploads, logs) and stores data in a
Microsoft SQL Server database.

## Stack

- Python 3.11+, Flask 3 (application-factory layout)
- SQLAlchemy 2 + Flask-SQLAlchemy + Flask-Migrate (Alembic migrations)
- MSSQL via **pyodbc** (ODBC Driver 18 for SQL Server)
- Gunicorn + systemd in production, Nginx as reverse proxy

## Project layout

```
riparazioni/
├── app/
│   ├── __init__.py        # create_app() factory: config, extensions, logging
│   ├── config.py          # settings from environment variables
│   ├── extensions.py      # SQLAlchemy + Flask-Migrate instances
│   ├── models/
│   │   ├── owned.py       # REPAIRS, REPAIR_WORK_LOG, REPAIR_PARTS, REFRIGERATORS,
│   │   │                  # GAS_CYLINDERS, SERVICE_PARTS, PICTURES (migrated)
│   │   └── external.py    # read-only DATIDBSTORICO: TBALLESTIMENTI, VICLIENTI, TBUSERS
│   ├── routes/
│   │   ├── health.py      # /healthz, /healthz/db
│   │   └── api/           # /api/v1: reference, equipment, pictures, repairs
│   ├── services/          # business logic: repairs (gas recharges), pictures (files)
│   ├── templates/
│   └── static/
├── migrations/            # Alembic migrations (flask-migrate)
├── tests/                 # pytest suite (runs without MSSQL)
├── var/                   # runtime-writable: uploads/, log/  (gitignored)
├── deploy/
│   ├── riparazioni.service   # systemd unit
│   ├── nginx.conf.example
│   └── install-mssql-odbc.sh # installs ODBC Driver 18 (Ubuntu/Debian)
├── wsgi.py                # gunicorn entry point (wsgi:app)
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── Makefile
```

## Development setup

```bash
make install-dev                 # creates .venv, installs dependencies
cp .env.example .env             # then edit DATABASE_URL for your MSSQL
sudo bash deploy/install-mssql-odbc.sh   # ODBC driver (also for local dev)
make run                         # flask run on http://127.0.0.1:5000
```

## API

A machine-readable OpenAPI 3.0 specification of all `/api/v1` endpoints is at
[`docs/openapi.yaml`](docs/openapi.yaml) (validated against the running app).

All endpoints live under `/api/v1` and return JSON. Errors use the envelope
`{"error": "message"}` with `400` (validation), `404` (unknown id / missing
file), `405` (writes to read-only resources), `409` (referential conflict).

### Health

- `GET /healthz` — liveness (process is up)
- `GET /healthz/db` — readiness (database reachable), 503 when not

### Reference data (read-only, legacy `DATIDBSTORICO`)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/vehicles` | List vehicles (`TBALLESTIMENTI`) |
| GET | `/api/v1/vehicles/<id>` | Vehicle detail (id = `ID_INT`) |
| GET | `/api/v1/customers` | List customers (`VICLIENTI` view) |
| GET | `/api/v1/customers/<id>` | Customer detail |
| GET | `/api/v1/users` | List users (`TBUSERS`, password never exposed) |
| GET | `/api/v1/users/<id>` | User detail (id = `ID_INT`) |

### Equipment (CRUD)

- `GET/POST /api/v1/refrigerators`, `GET/PUT/DELETE /api/v1/refrigerators/<id>`
- `GET/POST /api/v1/gas-cylinders`, `GET/PUT/DELETE /api/v1/gas-cylinders/<id>`
  — on create, `remaining_weight` defaults to `full_weight` when omitted
- `GET/POST /api/v1/service-parts`, `GET/PUT/DELETE /api/v1/service-parts/<id>`
  — list filter: `?is_refrigerator_part=true|false`

Deleting a record still referenced by a repair, work-log entry or picture
reference returns `409`.

### Pictures

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/pictures` | multipart upload (`file` field, optional `uploaded_by`) |
| GET | `/api/v1/pictures` | List pictures |
| GET | `/api/v1/pictures/<id>` | Picture metadata |
| GET | `/api/v1/pictures/<id>/file` | Download the stored file |
| DELETE | `/api/v1/pictures/<id>` | Delete record + file (409 while referenced) |

Files are stored as `UPLOAD_DIR/pictures/<uuid-hex><ext>`; `PICTURES.path`
keeps the relative path.

### Repairs

- `GET /api/v1/repairs` — list; filters: `customer`, `vehicle`,
  `refrigerator`, `type` (`RIPA`/`RIPA_FRIGO`), `start_date_from`,
  `start_date_to` (ISO 8601)
- `POST /api/v1/repairs` — create; body: `type` (required), `customer`,
  `vehicle`, `refrigerator`, `start_data`, `notes`, `parts`
- `GET /api/v1/repairs/<id>` — detail, includes `work_log` and `parts`
- `PUT /api/v1/repairs/<id>` — update; set `end_data` to complete, `null` to
  reopen; `parts` (when present) replaces the full part set
- `DELETE /api/v1/repairs/<id>` — delete; removes work log + parts and
  restores any cylinder balances recorded on its recharges

`customer`/`vehicle` are validated against the legacy reference data
(409 when unknown — no DB FK exists, `VICLIENTI` is a view).

**Parts payload** (create or update): `[{"id_part": 1, "quantity": 2,
"unit_price": 80}]` — `unit_price` optional.

### Work log (nested under a repair)

- `GET /api/v1/repairs/<id>/work-log` — list entries
- `POST /api/v1/repairs/<id>/work-log` — add entry: `start_time`, `end_time`,
  `operator` (ISO 8601), plus optional gas fields
- `PUT /api/v1/repairs/<id>/work-log/<entry_id>` — update (gas fields, when
  present, replace the entry's whole gas dataset and re-apply the balance)
- `DELETE /api/v1/repairs/<id>/work-log/<entry_id>` — delete; restores the
  cylinder balance when the entry recorded a recharge

**Gas fields**: `gas_system_state` (`VUOTO` | `PIENO` |
`RICUPERO_RICARICA`), `gas_recharge` (cylinder id),
`gas_recharge_weight` (float, kg), `gas_recovered_weight` (float, kg).

Recharge rules: a recharge needs both `gas_recharge` and
`gas_recharge_weight` (400 otherwise); a `RIPA_FRIGO` entry carrying gas
data needs `gas_system_state`; `PIENO` must not carry gas data; recharging
more than the cylinder's remaining weight is rejected (400); the balance is
decreased in the same transaction as the entry and restored when the entry
(or its parent repair) is deleted.

## Tests

The suite runs **without** MSSQL (in-memory SQLite with an attached
`DATIDBSTORICO` database faking the legacy schema):

```bash
make test
make lint
```

### Database migrations

`migrations/` contains the initial schema (the seven owned tables only —
`DATIDBSTORICO` objects are excluded via an `include_object` filter in
`env.py` and must never be created by this app). Apply with:

```bash
make db-upgrade                        # applies pending revisions
.venv/bin/flask db migrate -m "msg"    # autogenerate a new revision (models changed)
```

## MSSQL smoke checklist (first deploy / after DB changes)

The automated suite covers behavior on SQLite; run this against the real
database to verify the ODBC surface and the legacy schema (task 1.5 of the
`add-repair-management-api` change):

```bash
# 1. Connection + driver (adjust credentials)
sqlcmd -S <host> -U <user> -P <password> -C -Q "SELECT @@VERSION"

# 2. Apply the migration
/opt/riparazioni/.venv/bin/flask db upgrade

# 3. Owned tables exist, in the default schema
sqlcmd -S <host> -U <user> -P <password> -C -Q \
  "SELECT name FROM sys.tables WHERE name IN ('REPAIRS','REPAIR_WORK_LOG','REPAIR_PARTS','REFRIGERATORS','GAS_CYLINDERS','SERVICE_PARTS','PICTURES')"

# 4. External objects exist with the expected columns (compare against
#    app/models/external.py; fix model drift there, never in a migration)
sqlcmd -S <host> -U <user> -P <password> -C -Q \
  "SELECT c.name FROM sys.columns c JOIN sys.tables t ON c.object_id=t.object_id WHERE t.name='TBALLESTIMENTI' AND t.schema_id=SCHEMA_ID('DATIDBSTORICO') ORDER BY c.column_id"
sqlcmd -S <host> -U <user> -P <password> -C -Q \
  "SELECT c.name FROM sys.columns c JOIN sys.views v ON c.object_id=v.object_id WHERE v.name='VICLIENTI' AND v.schema_id=SCHEMA_ID('DATIDBSTORICO') ORDER BY c.column_id"
sqlcmd -S <host> -U <user> -P <password> -C -Q \
  "SELECT c.name FROM sys.columns c JOIN sys.tables t ON c.object_id=t.object_id WHERE t.name='TBUSERS' AND t.schema_id=SCHEMA_ID('DATIDBSTORICO') ORDER BY c.column_id"

# 5. One endpoint per group
curl -s http://127.0.0.1/healthz/db
curl -s http://127.0.0.1/api/v1/vehicles | head
curl -s http://127.0.0.1/api/v1/customers | head
curl -s http://127.0.0.1/api/v1/refrigerators
curl -s http://127.0.0.1/api/v1/gas-cylinders
curl -s http://127.0.0.1/api/v1/service-parts
curl -s http://127.0.0.1/api/v1/repairs
```

## Configuration

All settings come from environment variables (local `.env` or the systemd
environment file):

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | `development` | `development`, `testing`, `production` |
| `FLASK_DEBUG` | `0` | Debug mode |
| `SECRET_KEY` | dev placeholder | Set a long random value in production |
| `DATABASE_URL` | local MSSQL sample | `mssql+pyodbc://USER:PASS@HOST:1433/DB?driver=ODBC+Driver+18+for+SQL+Server` |
| `BASE_DIR` | project root | Base directory for runtime files |
| `UPLOAD_DIR` | `<BASE_DIR>/var/uploads` | Where the app writes uploaded files |
| `LOG_DIR` | `<BASE_DIR>/var/log` | Where `app.log` is written |
| `TEST_DATABASE_URL` | `sqlite://` | Test-suite database override |

URL-encode special characters in the MSSQL password (`%` → `%25`, etc.).

## Production deployment (Linux server)

The server runs gunicorn under systemd, bound to 127.0.0.1:8000, behind
Nginx. All filesystem writes happen under `/opt/riparazioni/var`.

1. **ODBC driver** (once, as root):

   ```bash
   sudo bash deploy/install-mssql-odbc.sh
   ```

2. **Service user and code**:

   ```bash
   sudo useradd -r -s /usr/sbin/nologin riparazioni
   sudo mkdir -p /opt/riparazioni
   sudo chown -R riparazioni:riparazioni /opt/riparazioni
   # copy the repository (without .venv) into /opt/riparazioni
   sudo -u riparazioni python3 -m venv /opt/riparazioni/.venv
   sudo -u riparazioni /opt/riparazioni/.venv/bin/pip install -r /opt/riparazioni/requirements.txt
   ```

3. **Environment file** (not in the repo):

   ```bash
   sudo install -d -m 750 -o root -g riparazioni /etc/riparazioni
   sudo cp .env.example /etc/riparazioni/riparazioni.env
   sudoedit /etc/riparazioni/riparazioni.env   # FLASK_ENV=production, real SECRET_KEY, DATABASE_URL, BASE_DIR=/opt/riparazioni
   sudo chmod 640 /etc/riparazioni/riparazioni.env
   ```

4. **Writable directories**:

   ```bash
   sudo mkdir -p /opt/riparazioni/var/uploads /opt/riparazioni/var/log
   sudo chown -R riparazioni:riparazioni /opt/riparazioni/var
   ```

5. **MSSQL**: create the database and a login for the app user with the
   grants it needs.

6. **Systemd**:

   ```bash
   sudo cp deploy/riparazioni.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now riparazioni
   journalctl -u riparazioni -f
   ```

7. **Nginx**:

   ```bash
   sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/riparazioni
   sudo ln -s ../sites-available/riparazioni /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```

8. **Verify**:

   ```bash
   curl http://127.0.0.1/healthz
   curl http://127.0.0.1/healthz/db
   ```

To release an update: pull the new code, then
`/opt/riparazioni/.venv/bin/pip install -r requirements.txt` (if changed),
run `db-upgrade` for migrations, and `sudo systemctl restart riparazioni`.
