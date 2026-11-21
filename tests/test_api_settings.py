"""Settings API tests (tasks 2.1-2.3).

Covers the settings capability spec: JSON-native read/write, known-key
defaults, validation of each known setting, atomic bulk updates, and delete.
"""


def _put(client, name, value):
    return client.put(f"/api/v1/settings/{name}", json=value)


# --- 2.2 reads ---------------------------------------------------------------


class TestReads:
    def test_list_includes_known_defaults_when_empty(self, client, db):
        response = client.get("/api/v1/settings")
        assert response.status_code == 200
        body = response.get_json()
        assert body["operators"] == []
        assert body["working_hours"] == {
            "mon": [],
            "tue": [],
            "wed": [],
            "thu": [],
            "fri": [],
            "sat": [],
            "sun": [],
        }
        assert body["holidays"] == {}

    def test_read_known_setting_default(self, client, db):
        response = client.get("/api/v1/settings/operators")
        assert response.status_code == 200
        assert response.get_json() == []

    def test_read_unknown_setting_404(self, client, db):
        response = client.get("/api/v1/settings/nope")
        assert response.status_code == 404
        assert set(response.get_json()) == {"error"}


# --- 2.2 writes --------------------------------------------------------------


class TestWrites:
    def test_upsert_single_and_read_back(self, client, db):
        response = _put(client, "operators", ["MARIO", "LUIGI"])
        assert response.status_code == 200
        assert response.get_json() == ["MARIO", "LUIGI"]
        assert client.get("/api/v1/settings/operators").get_json() == ["MARIO", "LUIGI"]

    def test_bulk_update(self, client, db):
        response = client.put(
            "/api/v1/settings",
            json={
                "operators": ["ANNA"],
                "holidays": {
                    "2026": [
                        {"from": "2026-01-01", "to": "2026-01-01", "name": "Capodanno"}
                    ]
                },
            },
        )
        assert response.status_code == 200
        body = client.get("/api/v1/settings").get_json()
        assert body["operators"] == ["ANNA"]
        assert body["holidays"]["2026"][0]["name"] == "Capodanno"

    def test_unknown_setting_accepts_any_json(self, client, db):
        response = _put(client, "custom", {"anything": [1, 2, 3]})
        assert response.status_code == 200
        assert client.get("/api/v1/settings/custom").get_json() == {"anything": [1, 2, 3]}

    def test_non_json_body_400(self, client, db):
        response = client.put(
            "/api/v1/settings/operators",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert set(response.get_json()) == {"error"}

    def test_bulk_body_must_be_object(self, client, db):
        response = client.put("/api/v1/settings", json=["operators"])
        assert response.status_code == 400


# --- 2.1 validators ----------------------------------------------------------


class TestValidation:
    def test_reject_invalid_operators(self, client, db):
        response = _put(client, "operators", ["ok", 3])
        assert response.status_code == 400
        assert client.get("/api/v1/settings/operators").get_json() == []

    def test_accept_valid_operators(self, client, db):
        assert _put(client, "operators", ["MARIO", "LUIGI"]).status_code == 200

    def test_reject_unknown_weekday(self, client, db):
        response = _put(client, "working_hours", {"funday": []})
        assert response.status_code == 400

    def test_reject_interval_begin_not_before_end(self, client, db):
        response = _put(client, "working_hours", {"mon": [["18:00", "08:00"]]})
        assert response.status_code == 400

    def test_reject_bad_time_format(self, client, db):
        response = _put(client, "working_hours", {"mon": [["8:00", "12:00"]]})
        assert response.status_code == 400

    def test_accept_valid_working_hours(self, client, db):
        value = {"mon": [["08:00", "12:00"], ["14:00", "18:00"]], "sun": []}
        response = _put(client, "working_hours", value)
        assert response.status_code == 200
        assert client.get("/api/v1/settings/working_hours").get_json() == value

    def test_reject_holiday_range_outside_year(self, client, db):
        response = _put(
            client,
            "holidays",
            {"2026": [{"from": "2026-12-28", "to": "2027-01-02", "name": "Fine anno"}]},
        )
        assert response.status_code == 400

    def test_reject_holiday_from_after_to(self, client, db):
        response = _put(
            client,
            "holidays",
            {"2026": [{"from": "2026-08-21", "to": "2026-08-10", "name": "X"}]},
        )
        assert response.status_code == 400

    def test_reject_holiday_missing_name(self, client, db):
        response = _put(
            client,
            "holidays",
            {"2026": [{"from": "2026-01-01", "to": "2026-01-01", "name": ""}]},
        )
        assert response.status_code == 400

    def test_reject_holiday_bad_year_key(self, client, db):
        response = _put(
            client,
            "holidays",
            {"26": [{"from": "2026-01-01", "to": "2026-01-01", "name": "X"}]},
        )
        assert response.status_code == 400

    def test_accept_valid_holidays(self, client, db):
        value = {"2026": [{"from": "2026-08-10", "to": "2026-08-21", "name": "Ferie"}]}
        assert _put(client, "holidays", value).status_code == 200
        assert client.get("/api/v1/settings/holidays").get_json() == value


# --- 2.3 atomic bulk update --------------------------------------------------


class TestBulkAtomic:
    def test_invalid_value_in_bulk_changes_nothing(self, client, db):
        assert _put(client, "operators", ["MARIO"]).status_code == 200

        response = client.put(
            "/api/v1/settings",
            json={
                "operators": ["LUIGI"],
                "holidays": {
                    "2026": [
                        {"from": "2027-01-01", "to": "2027-01-01", "name": "X"}
                    ]
                },
            },
        )
        assert response.status_code == 400
        # Nothing changed: operators keep the seeded value, holidays stay default.
        assert client.get("/api/v1/settings/operators").get_json() == ["MARIO"]
        assert client.get("/api/v1/settings/holidays").get_json() == {}


# --- 2.2 delete --------------------------------------------------------------


class TestDelete:
    def test_delete_known_reverts_to_default(self, client, db):
        _put(client, "operators", ["MARIO"])
        response = client.delete("/api/v1/settings/operators")
        assert response.status_code == 204
        assert client.get("/api/v1/settings/operators").get_json() == []

    def test_delete_unknown_404(self, client, db):
        response = client.delete("/api/v1/settings/nope")
        assert response.status_code == 404
