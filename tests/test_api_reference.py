"""Reference-data API tests (tasks 2.1-2.3)."""

from app.models import AppUser, Customer, Vehicle


def _seed_external(db):
    vehicle = Vehicle(
        ID_INT=7,
        ID="000000000000007",
        NOMINATIVO_ID="NOM7",
        TARGA="ZZZ999",
        AUTOCARRO="IVECO",
        CARROZZERIA="FURGONE",
        MODELLO="EURGO",
        CLASSE="N2",
    )
    customer = Customer(
        ID=9,
        N_NOMINATIVO=9,
        CLIENTE="Beta S.r.l.",
        NCLIENTE="C009",
        VIA="VIA MILANO 2",
        CITTA="MILANO",
    )
    user = AppUser(ID_INT=5, ID="000000000000005", NAME="ALICE", PASSWORD="hash")
    db.session.add_all([vehicle, customer, user])
    db.session.commit()
    return vehicle.ID_INT, customer.ID, user.ID_INT


class TestVehicles:
    def test_list_vehicles(self, client, db):
        vehicle_id, _, _ = _seed_external(db)
        response = client.get("/api/v1/vehicles")
        assert response.status_code == 200
        payload = response.get_json()
        assert isinstance(payload, list) and len(payload) == 2
        ids = [item["id"] for item in payload]
        assert vehicle_id in ids

    def test_vehicle_detail(self, client, db):
        vehicle_id, _, _ = _seed_external(db)
        response = client.get(f"/api/v1/vehicles/{vehicle_id}")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["id"] == vehicle_id
        assert payload["targa"] == "ZZZ999"

    def test_unknown_vehicle_404(self, client, db):
        response = client.get("/api/v1/vehicles/123456")
        assert response.status_code == 404
        assert "error" in response.get_json()

    def test_writes_rejected_405(self, client, db):
        assert client.post("/api/v1/vehicles", json={}).status_code == 405
        assert client.put("/api/v1/vehicles/1", json={}).status_code == 405
        assert client.delete("/api/v1/vehicles/1").status_code == 405


class TestCustomers:
    def test_list_customers(self, client, db):
        _, customer_id, _ = _seed_external(db)
        response = client.get("/api/v1/customers")
        assert response.status_code == 200
        payload = response.get_json()
        assert any(item["id"] == customer_id for item in payload)

    def test_customer_detail(self, client, db):
        _, customer_id, _ = _seed_external(db)
        response = client.get(f"/api/v1/customers/{customer_id}")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["id"] == customer_id
        assert payload["cliente"] == "Beta S.r.l."

    def test_unknown_customer_404(self, client, db):
        response = client.get("/api/v1/customers/123456")
        assert response.status_code == 404


class TestUsers:
    def test_list_users_excludes_password(self, client, db):
        _, _, user_id = _seed_external(db)
        response = client.get("/api/v1/users")
        assert response.status_code == 200
        payload = response.get_json()
        assert any(item["id"] == user_id for item in payload)

    def test_user_detail_excludes_password(self, client, db):
        _, _, user_id = _seed_external(db)
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["name"] == "ALICE"
        assert "password" not in {key.lower() for key in payload}

    def test_unknown_user_404(self, client, db):
        response = client.get("/api/v1/users/123456")
        assert response.status_code == 404
