"""Equipment CRUD API tests (tasks 3.1-3.3)."""

from app.models import RepairPart, Repairs, RepairWorkLog


def _new_repair(db, refrigerator_id=None):
    repair = Repairs(customer=1, vehicle=1, type="RIPA", refrigerator=refrigerator_id)
    db.session.add(repair)
    db.session.commit()
    return repair.id


class TestRefrigerators:
    def test_create(self, client, db):
        response = client.post(
            "/api/v1/refrigerators",
            json={"serial_nr": "SN-001", "model": "M", "brand": "B", "gas_kg": 1.5},
        )
        assert response.status_code == 201
        payload = response.get_json()
        assert payload["serial_nr"] == "SN-001"
        assert payload["id"] is not None

    def test_list(self, client, db):
        client.post("/api/v1/refrigerators", json={"serial_nr": "SN-A"})
        client.post("/api/v1/refrigerators", json={"serial_nr": "SN-B"})
        response = client.get("/api/v1/refrigerators")
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_detail_and_unknown(self, client, db):
        created = client.post("/api/v1/refrigerators", json={"serial_nr": "SN-C"}).get_json()
        response = client.get(f"/api/v1/refrigerators/{created['id']}")
        assert response.status_code == 200
        assert response.get_json()["serial_nr"] == "SN-C"
        assert client.get("/api/v1/refrigerators/99999").status_code == 404

    def test_update(self, client, db):
        created = client.post("/api/v1/refrigerators", json={"model": "OLD"}).get_json()
        response = client.put(
            f"/api/v1/refrigerators/{created['id']}", json={"model": "NEW"}
        )
        assert response.status_code == 200
        assert response.get_json()["model"] == "NEW"

    def test_delete_unreferenced(self, client, db):
        created = client.post("/api/v1/refrigerators", json={}).get_json()
        response = client.delete(f"/api/v1/refrigerators/{created['id']}")
        assert response.status_code == 204
        assert client.get(f"/api/v1/refrigerators/{created['id']}").status_code == 404

    def test_delete_referenced_conflict(self, client, db):
        created = client.post("/api/v1/refrigerators", json={}).get_json()
        _new_repair(db, refrigerator_id=created["id"])
        response = client.delete(f"/api/v1/refrigerators/{created['id']}")
        assert response.status_code == 409
        assert "error" in response.get_json()
        # Still present.
        assert client.get(f"/api/v1/refrigerators/{created['id']}").status_code == 200


class TestGasCylinders:
    def test_create_defaults_remaining_to_full(self, client, db):
        response = client.post(
            "/api/v1/gas-cylinders",
            json={"gas_kind": "R134a", "full_weight": 10.0},
        )
        assert response.status_code == 201
        payload = response.get_json()
        assert payload["full_weight"] == 10.0
        assert payload["remaining_weight"] == 10.0

    def test_create_explicit_remaining(self, client, db):
        response = client.post(
            "/api/v1/gas-cylinders",
            json={"gas_kind": "R600a", "full_weight": 10.0, "remaining_weight": 4.0},
        )
        assert response.get_json()["remaining_weight"] == 4.0

    def test_list(self, client, db):
        client.post("/api/v1/gas-cylinders", json={"gas_kind": "A"})
        client.post("/api/v1/gas-cylinders", json={"gas_kind": "B"})
        response = client.get("/api/v1/gas-cylinders")
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_detail_and_unknown(self, client, db):
        created = client.post("/api/v1/gas-cylinders", json={"gas_kind": "R134a"}).get_json()
        assert client.get(f"/api/v1/gas-cylinders/{created['id']}").status_code == 200
        assert client.get("/api/v1/gas-cylinders/99999").status_code == 404

    def test_update(self, client, db):
        created = client.post("/api/v1/gas-cylinders", json={}).get_json()
        response = client.put(
            f"/api/v1/gas-cylinders/{created['id']}", json={"gas_kind": "R290"}
        )
        assert response.status_code == 200
        assert response.get_json()["gas_kind"] == "R290"

    def test_delete_unreferenced(self, client, db):
        created = client.post("/api/v1/gas-cylinders", json={}).get_json()
        assert client.delete(f"/api/v1/gas-cylinders/{created['id']}").status_code == 204
        assert client.get(f"/api/v1/gas-cylinders/{created['id']}").status_code == 404

    def test_delete_referenced_conflict(self, client, db):
        created = client.post("/api/v1/gas-cylinders", json={}).get_json()
        repair_id = _new_repair(db)
        entry = RepairWorkLog(
            id_repairs=repair_id, gas_recharge=created["id"], gas_recharge_weight=1.0
        )
        db.session.add(entry)
        db.session.commit()
        response = client.delete(f"/api/v1/gas-cylinders/{created['id']}")
        assert response.status_code == 409


class TestServiceParts:
    def test_create(self, client, db):
        response = client.post(
            "/api/v1/service-parts",
            json={"name": "Compressor", "price": 100, "kind": "fridge"},
        )
        assert response.status_code == 201
        payload = response.get_json()
        assert payload["name"] == "Compressor"
        assert payload["is_refrigerator_part"] is False  # default

    def test_list_with_and_without_filter(self, client, db):
        client.post("/api/v1/service-parts", json={"name": "P1", "is_refrigerator_part": True})
        client.post("/api/v1/service-parts", json={"name": "P2"})
        all_parts = client.get("/api/v1/service-parts").get_json()
        assert len(all_parts) == 2
        filtered = client.get("/api/v1/service-parts?is_refrigerator_part=true").get_json()
        assert len(filtered) == 1
        assert filtered[0]["name"] == "P1"

    def test_detail_and_unknown(self, client, db):
        created = client.post("/api/v1/service-parts", json={"name": "P3"}).get_json()
        assert client.get(f"/api/v1/service-parts/{created['id']}").status_code == 200
        assert client.get("/api/v1/service-parts/99999").status_code == 404

    def test_update(self, client, db):
        created = client.post("/api/v1/service-parts", json={"price": 10}).get_json()
        response = client.put(f"/api/v1/service-parts/{created['id']}", json={"price": 20})
        assert response.status_code == 200
        assert response.get_json()["price"] == 20

    def test_delete_referenced_conflict(self, client, db):
        created = client.post("/api/v1/service-parts", json={"name": "Used"}).get_json()
        repair_id = _new_repair(db)
        db.session.add(RepairPart(id_repairs=repair_id, id_part=created["id"], quantity=1))
        db.session.commit()
        response = client.delete(f"/api/v1/service-parts/{created['id']}")
        assert response.status_code == 409
