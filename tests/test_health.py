"""Tests for the health endpoints."""


def test_healthz_returns_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["service"] == "riparazioni"


def test_healthz_db_returns_ok_when_reachable(client):
    response = client.get("/healthz/db")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["database"] == "reachable"
    assert payload["latency_ms"] >= 0
