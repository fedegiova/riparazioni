"""Repairs API tests (tasks 5.1-5.5).

Covers every scenario in the repairs capability spec: create/type,
retrieve, update, delete (cascade + balance restore), parts association,
work log, and gas-recharge bookkeeping.
"""
from datetime import UTC, datetime

from app.models import GasCylinder, Repairs, RepairWorkLog, ServicePart


def _now():
    return datetime.now(UTC).replace(tzinfo=None)


def _create_repair(client, **overrides):
    payload = {"type": "RIPA", "customer": 1, "vehicle": 1}
    payload.update(overrides)
    return client.post("/api/v1/repairs", json=payload)


def _cylinder(db, remaining=10.0):
    cyl = GasCylinder(gas_kind="R134a", full_weight=20.0, remaining_weight=remaining)
    db.session.add(cyl)
    db.session.commit()
    return cyl.id


# --- 5.1 error handlers --------------------------------------------------------

class TestErrors:
    def test_unknown_resource_404_envelope(self, client, db):
        response = client.get("/api/v1/repairs/99999")
        assert response.status_code == 404
        body = response.get_json()
        assert set(body) == {"error"}

    def test_fk_violating_write_409_envelope(self, client, db):
        # refrigerator FK is enforced by the DB; an unknown refrigerator -> 409
        response = client.post(
            "/api/v1/repairs",
            json={"type": "RIPA", "customer": 1, "vehicle": 1, "refrigerator": 99999},
        )
        assert response.status_code == 409
        assert set(response.get_json()) == {"error"}


# --- 5.2 repairs CRUD ----------------------------------------------------------

class TestCreate:
    def test_create_ripa_frigo(self, client, db):
        response = _create_repair(client, type="RIPA_FRIGO")
        assert response.status_code == 201
        payload = response.get_json()
        assert payload["id"] is not None
        assert payload["type"] == "RIPA_FRIGO"
        assert payload["start_data"] is not None

    def test_start_datetime_defaults_to_now(self, client, db):
        before = _now()
        payload = _create_repair(client).get_json()
        after = _now()
        assert payload["start_data"] is not None
        start = datetime.fromisoformat(payload["start_data"])
        assert before.replace(microsecond=0) <= start <= after + (
            _now() - after
        )

    def test_unknown_customer_rejected_409(self, client, db):
        response = _create_repair(client, customer=99999)
        assert response.status_code == 409
        count = db.session.execute(db.select(Repairs.id)).scalars().all()
        assert count == []

    def test_unknown_vehicle_rejected_409(self, client, db):
        assert _create_repair(client, vehicle=99999).status_code == 409

    def test_missing_type_rejected_400(self, client, db):
        response = client.post("/api/v1/repairs", json={"customer": 1, "vehicle": 1})
        assert response.status_code == 400


class TestType:
    def test_invalid_type_create_400(self, client, db):
        assert _create_repair(client, type="NOPE").status_code == 400

    def test_invalid_type_update_400(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        response = client.put(f"/api/v1/repairs/{repair_id}", json={"type": "BAD"})
        assert response.status_code == 400


class TestRetrieve:
    def test_list_all(self, client, db):
        _create_repair(client)
        _create_repair(client, type="RIPA_FRIGO")
        response = client.get("/api/v1/repairs")
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_filter_by_customer(self, client, db):
        _create_repair(client, customer=1)
        response = client.get("/api/v1/repairs?customer=1")
        assert all(item["customer"] == 1 for item in response.get_json())

    def test_filter_by_type(self, client, db):
        _create_repair(client, type="RIPA")
        _create_repair(client, type="RIPA_FRIGO")
        response = client.get("/api/v1/repairs?type=RIPA_FRIGO")
        body = response.get_json()
        assert len(body) == 1 and body[0]["type"] == "RIPA_FRIGO"

    def test_detail_includes_work_log_and_parts(self, client, db):
        part = ServicePart(name="P")
        _cylinder(db)
        db.session.add(part)
        db.session.commit()
        repair = _create_repair(
            client,
            parts=[{"id_part": part.id, "quantity": 2}],
        ).get_json()
        client.post(
            f"/api/v1/repairs/{repair['id']}/work-log",
            json={"start_time": "2026-01-01T08:00:00", "operator": "A"},
        )
        client.post(
            f"/api/v1/repairs/{repair['id']}/work-log",
            json={"operator": "B"},
        )

        detail = client.get(f"/api/v1/repairs/{repair['id']}").get_json()
        assert len(detail["work_log"]) == 2
        assert len(detail["parts"]) == 1
        assert detail["parts"][0]["quantity"] == 2

    def test_unknown_repair_404(self, client, db):
        assert client.get("/api/v1/repairs/99999").status_code == 404


class TestUpdate:
    def test_complete_repair(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        response = client.put(
            f"/api/v1/repairs/{repair_id}", json={"end_data": "2026-01-02T10:00:00"}
        )
        assert response.status_code == 200
        assert response.get_json()["end_data"] == "2026-01-02T10:00:00"

    def test_reopen_repair(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        client.put(f"/api/v1/repairs/{repair_id}", json={"end_data": "2026-01-02T10:00:00"})
        response = client.put(f"/api/v1/repairs/{repair_id}", json={"end_data": None})
        assert response.status_code == 200
        assert response.get_json()["end_data"] is None


class TestDelete:
    def test_cascade_work_log_and_parts(self, client, db):
        part = ServicePart(name="P")
        db.session.add(part)
        db.session.commit()
        repair_id = _create_repair(client, parts=[{"id_part": part.id, "quantity": 1}]).get_json()["id"]
        client.post(
            f"/api/v1/repairs/{repair_id}/work-log", json={"operator": "A"}
        )
        assert client.delete(f"/api/v1/repairs/{repair_id}").status_code == 204
        assert client.get(f"/api/v1/repairs/{repair_id}").status_code == 404
        assert db.session.execute(db.select(RepairWorkLog.id)).scalars().all() == []
        # The part itself survives (only the association is removed).
        assert db.session.execute(db.select(ServicePart.id)).scalars().all() == [part.id]


# --- 5.3 parts association -----------------------------------------------------

class TestParts:
    def test_create_with_parts(self, client, db):
        part = ServicePart(name="P")
        db.session.add(part)
        db.session.commit()
        payload = _create_repair(client, parts=[{"id_part": part.id, "quantity": 2}]).get_json()
        assert payload["parts"][0]["quantity"] == 2

    def test_unknown_part_409(self, client, db):
        response = _create_repair(client, parts=[{"id_part": 99999, "quantity": 1}])
        assert response.status_code == 409
        assert db.session.execute(db.select(Repairs.id)).scalars().all() == []

    def test_invalid_quantity_400(self, client, db):
        part = ServicePart(name="P")
        db.session.add(part)
        db.session.commit()
        response = _create_repair(client, parts=[{"id_part": part.id, "quantity": 0}])
        assert response.status_code == 400

    def test_parts_present_in_detail(self, client, db):
        part = ServicePart(name="P")
        db.session.add(part)
        db.session.commit()
        repair_id = _create_repair(
            client, parts=[{"id_part": part.id, "quantity": 3, "unit_price": 10}]
        ).get_json()["id"]
        detail = client.get(f"/api/v1/repairs/{repair_id}").get_json()
        assert detail["parts"][0]["quantity"] == 3
        assert detail["parts"][0]["unit_price"] == 10
        assert detail["parts"][0]["part"]["name"] == "P"


# --- 5.4 work log --------------------------------------------------------------

class TestWorkLog:
    def test_add_entry_201(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"start_time": "2026-01-01T08:00:00", "operator": "Alice"},
        )
        assert response.status_code == 201
        assert response.get_json()["operator"] == "Alice"

    def test_entry_visible_in_detail(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        client.post(f"/api/v1/repairs/{repair_id}/work-log", json={"operator": "A"})
        detail = client.get(f"/api/v1/repairs/{repair_id}").get_json()
        assert len(detail["work_log"]) == 1

    def test_update_entry(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        entry_id = client.post(
            f"/api/v1/repairs/{repair_id}/work-log", json={"operator": "A"}
        ).get_json()["id"]
        response = client.put(
            f"/api/v1/repairs/{repair_id}/work-log/{entry_id}", json={"operator": "Z"}
        )
        assert response.status_code == 200
        assert response.get_json()["operator"] == "Z"

    def test_delete_entry_204(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        entry_id = client.post(
            f"/api/v1/repairs/{repair_id}/work-log", json={"operator": "A"}
        ).get_json()["id"]
        response = client.delete(f"/api/v1/repairs/{repair_id}/work-log/{entry_id}")
        assert response.status_code == 204
        detail = client.get(f"/api/v1/repairs/{repair_id}").get_json()
        assert detail["work_log"] == []

    def test_work_log_unknown_repair_404(self, client, db):
        response = client.post("/api/v1/repairs/99999/work-log", json={"operator": "A"})
        assert response.status_code == 404


# --- 5.5 gas recharge ----------------------------------------------------------

class TestGasRecharge:
    def test_recharge_decreases_balance(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client, type="RIPA_FRIGO").get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={
                "gas_system_state": "VUOTO",
                "gas_recharge": cyl_id,
                "gas_recharge_weight": 2.5,
            },
        )
        assert response.status_code == 201
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 7.5

    def test_full_system_stores_no_gas_data(self, client, db):
        repair_id = _create_repair(client, type="RIPA_FRIGO").get_json()["id"]
        entry = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_system_state": "PIENO"},
        ).get_json()
        assert entry["gas_recharge"] is None
        assert entry["gas_recharge_weight"] is None

    def test_recovered_weight_stored_balance_only_recharge(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client, type="RIPA_FRIGO").get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={
                "gas_system_state": "RICUPERO_RICARICA",
                "gas_recharge": cyl_id,
                "gas_recharge_weight": 2.5,
                "gas_recovered_weight": 1.0,
            },
        )
        assert response.status_code == 201
        assert response.get_json()["gas_recovered_weight"] == 1.0
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 7.5

    def test_overdraw_rejected_balance_unchanged(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client, type="RIPA_FRIGO").get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_system_state": "VUOTO", "gas_recharge": cyl_id, "gas_recharge_weight": 12.0},
        )
        assert response.status_code == 400
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 10.0
        detail = client.get(f"/api/v1/repairs/{repair_id}").get_json()
        assert detail["work_log"] == []

    def test_recharge_without_cylinder_400(self, client, db):
        repair_id = _create_repair(client, type="RIPA_FRIGO").get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_system_state": "VUOTO", "gas_recharge_weight": 1.0},
        )
        assert response.status_code == 400

    def test_balance_restored_on_delete(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client, type="RIPA_FRIGO").get_json()["id"]
        entry_id = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_system_state": "VUOTO", "gas_recharge": cyl_id, "gas_recharge_weight": 2.5},
        ).get_json()["id"]
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 7.5
        client.delete(f"/api/v1/repairs/{repair_id}/work-log/{entry_id}")
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 10.0

    def test_repair_delete_restores_balance(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client, type="RIPA_FRIGO").get_json()["id"]
        client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_system_state": "VUOTO", "gas_recharge": cyl_id, "gas_recharge_weight": 2.5},
        )
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 7.5
        client.delete(f"/api/v1/repairs/{repair_id}")
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 10.0
