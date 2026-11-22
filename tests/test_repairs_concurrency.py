"""Independent-transaction checks for the repair mutation guard (task 5.1).

Each request runs in its own application context, session and SQLite
connection, so the two transactions genuinely interleave. The guard row makes
the outcomes deterministic: one writer holds the lock while the other waits,
then reads the committed state.
"""

import threading

import pytest
from sqlalchemy import event

from app import create_app
from app.extensions import db
from app.models import Customer, TransactionGuard, Vehicle


@pytest.fixture()
def file_app(tmp_path, monkeypatch):
    # TestingConfig's engine is created during create_app, so the URI and pool
    # must be set on the class before the app is built (a config override
    # afterwards keeps the in-memory StaticPool engine).
    from sqlalchemy.pool import QueuePool

    from app import config as config_module

    monkeypatch.setattr(
        config_module.TestingConfig,
        "SQLALCHEMY_DATABASE_URI",
        f"sqlite:///{tmp_path / 'concurrency.sqlite3'}",
    )
    monkeypatch.setattr(
        config_module.TestingConfig,
        "SQLALCHEMY_ENGINE_OPTIONS",
        {
            "poolclass": QueuePool,
            "connect_args": {"check_same_thread": False, "timeout": 20},
        },
        raising=False,
    )
    app = create_app("testing")
    app.config.update(
        TESTING=True,
        UPLOAD_DIR=tmp_path / "uploads",
        LOG_DIR=tmp_path / "log",
    )

    with app.app_context():
        # Give the legacy schema a real attached database, as the shared test
        # fixture does, so create_all can map the external tables. A file (not
        # :memory:) is required: the two requests use separate connections and
        # must see the same reference rows.
        external_path = str(tmp_path / "external.sqlite3")

        @event.listens_for(db.engine, "connect")
        def _setup_connection(dbapi_connection, connection_record):
            dbapi_connection.execute(
                f"ATTACH DATABASE '{external_path}' AS DATIDBSTORICO"
            )
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        db.metadata.create_all(db.engine)
        db.session.add_all(
            [
                Vehicle(
                    ID_INT=1,
                    ID="000000000000001",
                    NOMINATIVO_ID="NOM0000000000001",
                    TARGA="ABC123",
                    AUTOCARRO="FIAT",
                    CARROZZERIA="FURGONE",
                    MODELLO="DUCATO",
                    CLASSE="N1",
                    PROGRESSIVO=1,
                ),
                Customer(
                    ID=1,
                    N_NOMINATIVO=1,
                    CLIENTE="ACME SRL",
                    NCLIENTE="C001",
                ),
                TransactionGuard(id=1, version=0),
            ]
        )
        db.session.commit()
    return app


def _create_repair(app) -> int:
    with app.app_context():
        response = app.test_client().post(
            "/api/v1/repairs", json={"customer": 1, "vehicle": 1}
        )
        assert response.status_code == 201
        repair_id = response.get_json()["id"]
        db.session.remove()
        return repair_id


def _run_together(app, first, second):
    """Run two request callables at the same moment; return both responses."""
    barrier = threading.Barrier(2)
    results = {}

    def worker(key, call):
        with app.app_context():
            try:
                barrier.wait(timeout=10)
                results[key] = call(app.test_client())
            except Exception as exc:  # surfaced by the assertions below
                results[key] = exc
            finally:
                db.session.remove()

    threads = [
        threading.Thread(target=worker, args=("first", first)),
        threading.Thread(target=worker, args=("second", second)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    return results["first"], results["second"]


def _add_running_log(repair_id, start):
    return lambda client: client.post(
        f"/api/v1/repairs/{repair_id}/work-log",
        json={"operator": "FABRI", "start_time": start},
    )


def _archive(repair_id):
    return lambda client: client.put(
        f"/api/v1/repairs/{repair_id}", json={"end_data": "2026-01-01T18:00:00"}
    )


def test_concurrent_starts_leave_at_most_one_running_timer(file_app):
    repair_id = _create_repair(file_app)
    with file_app.app_context():
        first, second = _run_together(
            file_app,
            _add_running_log(repair_id, "2026-01-01T08:00:00"),
            _add_running_log(repair_id, "2026-01-01T09:00:00"),
        )
        assert {first.status_code, second.status_code} <= {201, 409}, (
            first.status_code,
            first.get_json(),
            second.status_code,
            second.get_json(),
        )
        assert 201 in {first.status_code, second.status_code}

        detail = file_app.test_client().get(f"/api/v1/repairs/{repair_id}").get_json()
        running = [
            entry
            for entry in detail["work_log"]
            if entry["start_time"] is not None and entry["end_time"] is None
        ]
        assert len(running) == 1
        db.session.remove()


def test_archive_and_start_cannot_both_succeed(file_app):
    repair_id = _create_repair(file_app)
    with file_app.app_context():
        archived, started = _run_together(
            file_app, _archive(repair_id), _add_running_log(repair_id, "2026-01-01T09:00:00")
        )
        assert archived.status_code != started.status_code
        assert {archived.status_code, started.status_code} in (
            {200, 409},
            {201, 409},
        )
        assert archived.status_code == 409 or started.status_code == 409

        detail = file_app.test_client().get(f"/api/v1/repairs/{repair_id}").get_json()
        running = [
            entry
            for entry in detail["work_log"]
            if entry["start_time"] is not None and entry["end_time"] is None
        ]
        # A repair can never end up archived while a timer is still running.
        assert not (detail["end_data"] is not None and running)

        if archived.status_code == 200:
            assert detail["end_data"] is not None
            assert running == []
            assert detail["total_hours"] == 0.0
        else:
            assert detail["end_data"] is None
            assert len(running) == 1
        db.session.remove()