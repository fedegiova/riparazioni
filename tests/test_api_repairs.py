"""Repairs API tests (tasks 5.1-5.5).

Covers every scenario in the repairs capability spec: create/delivery date,
retrieve, update, delete (cascade + balance restore), parts association,
work log, and gas-recharge bookkeeping.
"""
from datetime import datetime
from io import BytesIO

from openpyxl import load_workbook
from PIL import Image

from app.models import Customer, GasCylinder, Repairs, RepairWorkLog, ServicePart


def _now():
    return datetime.now().replace(tzinfo=None)


def _jpeg_bytes(size=(64, 64)):
    buffer = BytesIO()
    Image.new("RGB", size, (10, 20, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _create_repair(client, **overrides):
    payload = {"customer": 1, "vehicle": 1}
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
            json={"customer": 1, "vehicle": 1, "refrigerator": 99999},
        )
        assert response.status_code == 409
        assert set(response.get_json()) == {"error"}


# --- 5.2 repairs CRUD ----------------------------------------------------------

class TestCreate:
    def test_create_with_delivery_date(self, client, db):
        response = _create_repair(client, delivery_date="2026-08-01")
        assert response.status_code == 201
        payload = response.get_json()
        assert payload["id"] is not None
        assert payload["delivery_date"] == "2026-08-01"
        assert payload["start_data"] is not None
        # The removed type field is gone from the response shape.
        assert "type" not in payload

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


class TestRetrieve:
    def test_list_all(self, client, db):
        _create_repair(client)
        _create_repair(client)
        response = client.get("/api/v1/repairs")
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_filter_by_customer(self, client, db):
        _create_repair(client, customer=1)
        response = client.get("/api/v1/repairs?customer=1")
        assert all(item["customer"] == 1 for item in response.get_json())

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

    def test_detail_includes_pictures_and_list_omits_them(self, client, db):
        repair = _create_repair(client).get_json()
        upload = client.post(
            "/api/v1/pictures",
            data={
                "file": (BytesIO(_jpeg_bytes()), "p.jpg"),
                "owner_type": "repair",
                "owner_id": str(repair["id"]),
            },
            content_type="multipart/form-data",
        )
        assert upload.status_code == 201

        detail = client.get(f"/api/v1/repairs/{repair['id']}").get_json()
        assert [item["id"] for item in detail["pictures"]] == [
            upload.get_json()["id"]
        ]

        listing = client.get("/api/v1/repairs").get_json()
        assert "pictures" not in listing[0]

    def test_unknown_repair_404(self, client, db):
        assert client.get("/api/v1/repairs/99999").status_code == 404


# --- computed list/detail fields -----------------------------------------------

class TestComputedFields:
    def test_total_hours_sums_work_log_durations(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"start_time": "2026-01-01T08:00:00", "end_time": "2026-01-01T09:30:00"},
        )
        client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"start_time": "2026-01-01T10:00:00", "end_time": "2026-01-01T12:00:00"},
        )

        detail = client.get(f"/api/v1/repairs/{repair_id}").get_json()
        assert detail["total_hours"] == 3.5  # 1h30 + 2h00

        listing = client.get("/api/v1/repairs").get_json()
        row = next(item for item in listing if item["id"] == repair_id)
        assert row["total_hours"] == 3.5

    def test_null_duration_entries_contribute_zero(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        # An open entry (start only) and an empty entry: both contribute zero.
        client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"start_time": "2026-01-01T08:00:00"},
        )
        client.post(f"/api/v1/repairs/{repair_id}/work-log", json={"operator": "B"})

        detail = client.get(f"/api/v1/repairs/{repair_id}").get_json()
        assert detail["total_hours"] == 0.0

    def test_gas_used_sums_recharges(self, client, db):
        cyl_id = _cylinder(db, remaining=20.0)
        repair_id = _create_repair(client).get_json()["id"]
        for weight in (2.5, 1.0):
            client.post(
                f"/api/v1/repairs/{repair_id}/work-log",
                json={
                    "gas_system_state": "VUOTO",
                    "gas_recharge": cyl_id,
                    "gas_recharge_weight": weight,
                },
            )
        detail = client.get(f"/api/v1/repairs/{repair_id}").get_json()
        assert detail["gas_used"] == 3.5

        listing = client.get("/api/v1/repairs").get_json()
        row = next(item for item in listing if item["id"] == repair_id)
        assert row["gas_used"] == 3.5

    def test_gas_used_zero_without_gas_records(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        detail = client.get(f"/api/v1/repairs/{repair_id}").get_json()
        assert detail["gas_used"] == 0

    def test_customer_name_resolved_from_reference_data(self, client, db):
        created = _create_repair(client, customer=1).get_json()
        # The seeded VICLIENTI shim row (id 1) is ACME SRL.
        assert created["customer_name"] == "ACME SRL"

        listing = client.get("/api/v1/repairs").get_json()
        row = next(item for item in listing if item["id"] == created["id"])
        assert row["customer_name"] == "ACME SRL"

        detail = client.get(f"/api/v1/repairs/{created['id']}").get_json()
        assert detail["customer_name"] == "ACME SRL"

    def test_customer_name_null_when_id_has_no_record(self, client, db):
        # Insert directly: the API would reject an unknown customer (409).
        repair = Repairs(customer=999, vehicle=1)
        db.session.add(repair)
        db.session.commit()

        detail = client.get(f"/api/v1/repairs/{repair.id}").get_json()
        assert detail["customer_name"] is None

        listing = client.get("/api/v1/repairs").get_json()
        row = next(item for item in listing if item["id"] == repair.id)
        assert row["customer_name"] is None


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

    def test_change_delivery_date(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        response = client.put(
            f"/api/v1/repairs/{repair_id}", json={"delivery_date": "2026-09-15"}
        )
        assert response.status_code == 200
        assert response.get_json()["delivery_date"] == "2026-09-15"


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
        repair_id = _create_repair(client).get_json()["id"]
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
        repair_id = _create_repair(client).get_json()["id"]
        entry = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_system_state": "PIENO"},
        ).get_json()
        assert entry["gas_recharge"] is None
        assert entry["gas_recharge_weight"] is None

    def test_ricupero_ricarica_applies_net(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client).get_json()["id"]
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
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 8.5

    def test_recovery_increases_balance(self, client, db):
        cyl_id = _cylinder(db, remaining=4.0)
        repair_id = _create_repair(client).get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={
                "gas_system_state": "RECUPERO",
                "gas_recharge": cyl_id,
                "gas_recovered_weight": 1.0,
            },
        )
        assert response.status_code == 201
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 5.0

    def test_overdraw_rejected_balance_unchanged(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client).get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_system_state": "VUOTO", "gas_recharge": cyl_id, "gas_recharge_weight": 12.0},
        )
        assert response.status_code == 400
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 10.0
        detail = client.get(f"/api/v1/repairs/{repair_id}").get_json()
        assert detail["work_log"] == []

    def test_recharge_without_cylinder_400(self, client, db):
        repair_id = _create_repair(client).get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_system_state": "VUOTO", "gas_recharge_weight": 1.0},
        )
        assert response.status_code == 400

    def test_recovery_only_entry_accepted(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client).get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={
                "gas_system_state": "RECUPERO",
                "gas_recharge": cyl_id,
                "gas_recovered_weight": 1.0,
            },
        )
        assert response.status_code == 201
        payload = response.get_json()
        assert payload["gas_recovered_weight"] == 1.0
        assert payload["gas_recharge_weight"] is None

    def test_recovery_with_recharge_weight_rejected(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client).get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={
                "gas_system_state": "RECUPERO",
                "gas_recharge": cyl_id,
                "gas_recharge_weight": 1.0,
                "gas_recovered_weight": 1.0,
            },
        )
        assert response.status_code == 400

    def test_ricupero_ricarica_requires_recovered(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client).get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={
                "gas_system_state": "RICUPERO_RICARICA",
                "gas_recharge": cyl_id,
                "gas_recharge_weight": 1.0,
            },
        )
        assert response.status_code == 400

    def test_vuoto_with_recovered_rejected(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client).get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={
                "gas_system_state": "VUOTO",
                "gas_recharge": cyl_id,
                "gas_recharge_weight": 1.0,
                "gas_recovered_weight": 1.0,
            },
        )
        assert response.status_code == 400

    def test_overfill_rejected_balance_unchanged(self, client, db):
        cyl_id = _cylinder(db, remaining=19.0)
        repair_id = _create_repair(client).get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={
                "gas_system_state": "RECUPERO",
                "gas_recharge": cyl_id,
                "gas_recovered_weight": 2.0,
            },
        )
        assert response.status_code == 400
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 19.0

    def test_gas_data_without_state_rejected(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client).get_json()["id"]
        response = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_recharge": cyl_id, "gas_recharge_weight": 1.0},
        )
        assert response.status_code == 400
        # The balance is untouched and no entry was created.
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 10.0
        detail = client.get(f"/api/v1/repairs/{repair_id}").get_json()
        assert detail["work_log"] == []

    def test_balance_restored_on_delete(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client).get_json()["id"]
        entry_id = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_system_state": "VUOTO", "gas_recharge": cyl_id, "gas_recharge_weight": 2.5},
        ).get_json()["id"]
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 7.5
        client.delete(f"/api/v1/repairs/{repair_id}/work-log/{entry_id}")
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 10.0

    def test_delete_reverses_recovery_and_recharge(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client).get_json()["id"]
        entry_id = client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={
                "gas_system_state": "RICUPERO_RICARICA",
                "gas_recharge": cyl_id,
                "gas_recharge_weight": 2.5,
                "gas_recovered_weight": 1.0,
            },
        ).get_json()["id"]
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 8.5
        client.delete(f"/api/v1/repairs/{repair_id}/work-log/{entry_id}")
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 10.0

    def test_repair_delete_restores_balance(self, client, db):
        cyl_id = _cylinder(db, remaining=10.0)
        repair_id = _create_repair(client).get_json()["id"]
        client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={"gas_system_state": "VUOTO", "gas_recharge": cyl_id, "gas_recharge_weight": 2.5},
        )
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 7.5
        client.delete(f"/api/v1/repairs/{repair_id}")
        assert db.session.get(GasCylinder, cyl_id).remaining_weight == 10.0


# --- Excel export --------------------------------------------------------------

XLSX_MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class TestExport:
    def test_export_all_repairs_one_row_each(self, client, db):
        _create_repair(client)
        _create_repair(client)
        response = client.get("/api/v1/repairs/export")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == XLSX_MIMETYPE
        assert "attachment" in response.headers["Content-Disposition"]

        sheet = load_workbook(BytesIO(response.data)).active
        assert sheet.max_row == 3  # header + two repairs
        assert sheet.cell(row=1, column=1).value == "id"

    def test_export_includes_gas_used_column(self, client, db):
        cyl_id = _cylinder(db, remaining=20.0)
        repair_id = _create_repair(client).get_json()["id"]
        client.post(
            f"/api/v1/repairs/{repair_id}/work-log",
            json={
                "gas_system_state": "VUOTO",
                "gas_recharge": cyl_id,
                "gas_recharge_weight": 2.5,
            },
        )
        response = client.get("/api/v1/repairs/export")
        sheet = load_workbook(BytesIO(response.data)).active
        headers = [cell.value for cell in sheet[1]]
        assert "gas_used" in headers
        column = headers.index("gas_used") + 1
        assert sheet.cell(row=2, column=column).value == 2.5

    def test_export_honors_filters(self, client, db):
        db.session.add(
            Customer(ID=2, N_NOMINATIVO=2, CLIENTE="BETA SNC", NCLIENTE="C002")
        )
        db.session.commit()
        _create_repair(client, customer=1)
        _create_repair(client, customer=2)

        response = client.get("/api/v1/repairs/export?customer=2")
        assert response.status_code == 200
        sheet = load_workbook(BytesIO(response.data)).active
        assert sheet.max_row == 2  # header + the one matching repair
        assert sheet.cell(row=2, column=2).value == 2
