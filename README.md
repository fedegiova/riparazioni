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
│   ├── models/            # SQLAlchemy models (domain features go here)
│   ├── routes/            # blueprints (health checks for now)
│   ├── services/          # business logic layer
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

Endpoints:

- `GET /healthz` — liveness (process is up)
- `GET /healthz/db` — readiness (database reachable), 503 when not

Tests do **not** need MSSQL (in-memory SQLite by default):

```bash
make test
make lint
```

### Database migrations

`migrations/` is already initialised. Once you add models:

```bash
make db-migrate m="add riparazioni table"   # writes a new revision
make db-upgrade                             # applies it
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
