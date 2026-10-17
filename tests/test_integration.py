"""End-to-end integration test (task 6.1).

Walks the full RIPA FRIGO workflow over HTTP: create repair -> work-log
entry with a gas recharge -> assert cylinder balance -> add a part ->
complete the repair -> list filtered by customer.
"""


def test_ripa_frigo_full_workflow(client, db):

    # Master data
    cyl_id = client.post(
        "/api/v1/gas-cylinders",
        json={"gas_kind": "R134a", "full_weight": 10.0},
    ).get_json()["id"]
    part_id = client.post(
        "/api/v1/service-parts",
        json={"name": "Compressore", "price": 80, "is_refrigerator_part": True},
    ).get_json()["id"]

    # 1. Create the repair
    repair = client.post(
        "/api/v1/repairs",
        json={"type": "RIPA_FRIGO", "customer": 1, "vehicle": 1, "refrigerator": None},
    ).get_json()
    assert repair["type"] == "RIPA_FRIGO"
    assert repair["customer"] == 1

    # 2. Work-log entry with a gas recharge (impianto vuoto)
    entry = client.post(
        f"/api/v1/repairs/{repair['id']}/work-log",
        json={
            "start_time": "2026-10-08T08:00:00",
            "end_time": "2026-10-08T10:30:00",
            "operator": "Marco",
            "gas_system_state": "VUOTO",
            "gas_recharge": cyl_id,
            "gas_recharge_weight": 2.5,
        },
    ).get_json()
    assert entry["gas_recharge"] == cyl_id

    # 3. Cylinder balance decreased by exactly the recharged weight
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
