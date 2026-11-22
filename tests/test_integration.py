"""End-to-end integration test (task 6.1).

Walks the full repair workflow over HTTP: install a refrigerator, create a
repair, record a gas fill -> assert cylinder balance -> add a part ->
complete the repair -> list filtered by customer.
"""


def test_ripa_frigo_full_workflow(client, db):
    # Master data: a cylinder and the refrigerator installed on vehicle 1.
    cyl_id = client.post(
        "/api/v1/gas-cylinders",
        json={"gas_kind": "R32", "full_weight": 10.0},
    ).get_json()["id"]
    fridge_id = client.post(
        "/api/v1/refrigerators",
        json={
            "serial_nr": "SN-1",
            "brand": "B",
            "model": "M",
            "gas_kind": "R32",
            "gas_kg": 3.0,
            "allestimento_id": 1,
        },
    ).get_json()["id"]
    part_id = client.post(
        "/api/v1/service-parts",
        json={"name": "Compressore", "price": 80, "is_refrigerator_part": True},
    ).get_json()["id"]

    # 1. Create the repair
    repair = client.post(
        "/api/v1/repairs",
        json={"customer": 1, "vehicle": 1, "refrigerator": None, "delivery_date": "2026-10-10"},
    ).get_json()
    assert repair["delivery_date"] == "2026-10-10"
    assert repair["customer"] == 1
    assert repair["gas_equipment_locked"] is False

    # 2. Work-log entry that fills the gas system; the first gas operation
    #    locks the installed refrigerator to the repair.
    entry = client.post(
        f"/api/v1/repairs/{repair['id']}/work-log",
        json={
            "start_time": "2026-10-08T08:00:00",
            "end_time": "2026-10-08T10:30:00",
            "operator": "FABRI",
            "gas_operation": "fill",
            "gas_recharge": cyl_id,
            "gas_measured_kg": 2.5,
        },
    ).get_json()
    assert entry["gas_recharge"] == cyl_id
    assert entry["gas_operation"] == "fill"

    detail = client.get(f"/api/v1/repairs/{repair['id']}").get_json()
    assert detail["gas_equipment_locked"] is True
    assert detail["refrigerator"] == fridge_id
    assert detail["refrigerator_installed"] is True

    # 3. Cylinder balance decreased by exactly the added weight
    cylinder = client.get(f"/api/v1/gas-cylinders/{cyl_id}").get_json()
    assert cylinder["remaining_weight"] == 7.5

    # 4. Add a part (via update)
    updated = client.put(
        f"/api/v1/repairs/{repair['id']}",
        json={"parts": [{"id_part": part_id, "quantity": 2, "unit_price": 80}]},
    ).get_json()
    assert updated["parts"][0]["quantity"] == 2
    assert updated["parts"][0]["part"]["name"] == "Compressore"

    # 5. Complete the repair
    completed = client.put(
        f"/api/v1/repairs/{repair['id']}", json={"end_data": "2026-10-08T12:00:00"}
    ).get_json()
    assert completed["end_data"] == "2026-10-08T12:00:00"

    # 6. List filtered by customer; the repair is there with everything attached
    listing = client.get("/api/v1/repairs?customer=1").get_json()
    found = [item for item in listing if item["id"] == repair["id"]]
    assert len(found) == 1
    detail = client.get(f"/api/v1/repairs/{repair['id']}").get_json()
    assert len(detail["work_log"]) == 1
    assert len(detail["parts"]) == 1
    assert detail["end_data"] is not None


def test_gas_replacement_and_reversal_flow(client, db):
    """Install -> first gas log -> replace unit -> blocked -> reverse on delete."""
    from app.models import GasCylinder

    cyl_id = client.post(
        "/api/v1/gas-cylinders",
        json={"gas_kind": "R32", "full_weight": 10.0, "remaining_weight": 4.0},
    ).get_json()["id"]
    first = client.post(
        "/api/v1/refrigerators",
        json={
            "serial_nr": "FR-A",
            "brand": "B",
            "model": "M",
            "gas_kind": "R32",
            "gas_kg": 3.0,
            "allestimento_id": 1,
        },
    ).get_json()

    repair = client.post(
        "/api/v1/repairs", json={"customer": 1, "vehicle": 1}
    ).get_json()

    # First gas operation locks the installed unit and credits the recovery.
    entry = client.post(
        f"/api/v1/repairs/{repair['id']}/work-log",
        json={
            "operator": "FABRI",
            "gas_operation": "recovery",
            "gas_recharge": cyl_id,
            "gas_measured_kg": 2.0,
        },
    ).get_json()
    assert db.session.get(GasCylinder, cyl_id).remaining_weight == 6.0
    detail = client.get(f"/api/v1/repairs/{repair['id']}").get_json()
    assert detail["refrigerator"] == first["id"]
    assert detail["refrigerator_installed"] is True

    # Install a replacement on the same allestimento.
    replacement = client.post(
        "/api/v1/refrigerators",
        json={
            "serial_nr": "FR-B",
            "brand": "B",
            "model": "M",
            "gas_kind": "R32",
            "gas_kg": 3.0,
        },
    ).get_json()
    assert client.post(
        f"/api/v1/refrigerators/{replacement['id']}/install",
        json={"allestimento_id": 1},
    ).status_code == 200

    # The repair keeps its recorded unit, now flagged as not installed, and
    # further gas work is refused.
    detail = client.get(f"/api/v1/repairs/{repair['id']}").get_json()
    assert detail["refrigerator"] == first["id"]
    assert detail["refrigerator_installed"] is False
    blocked = client.post(
        f"/api/v1/repairs/{repair['id']}/work-log",
        json={
            "operator": "FABRI",
            "gas_operation": "recovery",
            "gas_recharge": cyl_id,
            "gas_measured_kg": 1.0,
        },
    )
    assert blocked.status_code == 409

    # Deleting the entry reverses the movement.
    client.delete(f"/api/v1/repairs/{repair['id']}/work-log/{entry['id']}")
    assert db.session.get(GasCylinder, cyl_id).remaining_weight == 4.0
