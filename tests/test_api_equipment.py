"""Equipment CRUD API tests (tasks 3.1-3.3)."""

from app.models import RepairPart, Repairs, RepairWorkLog


def _new_repair(db, refrigerator_id=None):
    repair = Repairs(customer=1, vehicle=1, refrigerator=refrigerator_id)
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
    def test_create_without_full_weight_rejected(self, client, db):
        response = client.post(
            "/api/v1/gas-cylinders", json={"gas_kind": "R134a"}
        )
        assert response.status_code == 400
        assert "full_weight" in response.get_json()["error"]

    def test_update_to_null_full_weight_rejected(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders", json={"full_weight": 10.0}
        ).get_json()
        response = client.put(
            f"/api/v1/gas-cylinders/{created['id']}", json={"full_weight": None}
        )
        assert response.status_code == 400

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
        client.post("/api/v1/gas-cylinders", json={"gas_kind": "A", "full_weight": 10.0})
        client.post("/api/v1/gas-cylinders", json={"gas_kind": "B", "full_weight": 10.0})
        response = client.get("/api/v1/gas-cylinders")
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_detail_and_unknown(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders", json={"gas_kind": "R134a", "full_weight": 10.0}
        ).get_json()
        assert client.get(f"/api/v1/gas-cylinders/{created['id']}").status_code == 200
        assert client.get("/api/v1/gas-cylinders/99999").status_code == 404

    def test_update(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders", json={"full_weight": 10.0}
        ).get_json()
        response = client.put(
            f"/api/v1/gas-cylinders/{created['id']}", json={"gas_kind": "R290"}
        )
        assert response.status_code == 200
        assert response.get_json()["gas_kind"] == "R290"

    def test_delete_unreferenced(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders", json={"full_weight": 10.0}
        ).get_json()
        assert client.delete(f"/api/v1/gas-cylinders/{created['id']}").status_code == 204
        assert client.get(f"/api/v1/gas-cylinders/{created['id']}").status_code == 404

    def test_delete_referenced_conflict(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders", json={"full_weight": 10.0}
        ).get_json()
        repair_id = _new_repair(db)
        entry = RepairWorkLog(
            id_repairs=repair_id, gas_recharge=created["id"], gas_recharge_weight=1.0
        )
        db.session.add(entry)
        db.session.commit()
        response = client.delete(f"/api/v1/gas-cylinders/{created['id']}")
        assert response.status_code == 409

    def test_archive_below_quarter(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders",
            json={"full_weight": 10.0, "remaining_weight": 2.0},
        ).get_json()
        response = client.post(f"/api/v1/gas-cylinders/{created['id']}/archive")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["archived"] is True
        assert payload["remaining_weight"] == 2.0

    def test_archive_at_or_above_quarter_rejected(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders",
            json={"full_weight": 10.0, "remaining_weight": 2.5},
        ).get_json()
        response = client.post(f"/api/v1/gas-cylinders/{created['id']}/archive")
        assert response.status_code == 400
        assert client.get(f"/api/v1/gas-cylinders/{created['id']}").get_json()[
            "archived"
        ] is False

    def test_restore_keeps_balance(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders",
            json={"full_weight": 10.0, "remaining_weight": 2.0},
        ).get_json()
        client.post(f"/api/v1/gas-cylinders/{created['id']}/archive")
        response = client.post(f"/api/v1/gas-cylinders/{created['id']}/restore")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["archived"] is False
        assert payload["remaining_weight"] == 2.0

    def test_refill_restores_full_weight(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders",
            json={"full_weight": 10.0, "remaining_weight": 2.0},
        ).get_json()
        response = client.post(
            f"/api/v1/gas-cylinders/{created['id']}/refills",
            json={"date": "2026-02-01", "reference": "RIF-1"},
        )
        assert response.status_code == 201
        cylinder = client.get(f"/api/v1/gas-cylinders/{created['id']}").get_json()
        assert cylinder["remaining_weight"] == 10.0

    def test_refill_unarchives_cylinder(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders",
            json={"full_weight": 10.0, "remaining_weight": 2.0},
        ).get_json()
        client.post(f"/api/v1/gas-cylinders/{created['id']}/archive")
        client.post(f"/api/v1/gas-cylinders/{created['id']}/refills", json={})
        cylinder = client.get(f"/api/v1/gas-cylinders/{created['id']}").get_json()
        assert cylinder["archived"] is False

    def test_refills_are_listed(self, client, db):
        created = client.post(
            "/api/v1/gas-cylinders", json={"full_weight": 10.0}
        ).get_json()
        client.post(
            f"/api/v1/gas-cylinders/{created['id']}/refills",
            json={"date": "2026-02-01", "reference": "RIF-1"},
        )
        response = client.get(f"/api/v1/gas-cylinders/{created['id']}/refills")
        assert response.status_code == 200
        refills = response.get_json()
        assert len(refills) == 1
        assert refills[0]["date"] == "2026-02-01"
        assert refills[0]["reference"] == "RIF-1"

    def test_archived_cylinders_hidden_by_default(self, client, db):
        active = client.post(
            "/api/v1/gas-cylinders", json={"full_weight": 10.0}
        ).get_json()
        to_archive = client.post(
            "/api/v1/gas-cylinders",
            json={"full_weight": 10.0, "remaining_weight": 2.0},
        ).get_json()
        client.post(f"/api/v1/gas-cylinders/{to_archive['id']}/archive")

        default = client.get("/api/v1/gas-cylinders").get_json()
        assert [cylinder["id"] for cylinder in default] == [active["id"]]

        all_items = client.get("/api/v1/gas-cylinders?archived=true").get_json()
        assert {cylinder["id"] for cylinder in all_items} == {
            active["id"],
            to_archive["id"],
        }


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
