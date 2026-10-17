"""Read-only reference data from the legacy DATIDBSTORICO objects.

Only GET endpoints are defined here; any other method is rejected by Flask
with 405 (rendered as the JSON error envelope by the API error handlers).
"""

from flask import jsonify

from app.extensions import db
from app.models import AppUser, Customer, Vehicle
from app.routes.api import bp
from app.services.errors import NotFound


@bp.get("/vehicles")
def list_vehicles():
    vehicles = (
        db.session.execute(db.select(Vehicle).order_by(Vehicle.ID_INT)).scalars()
    )
    return jsonify([vehicle.to_dict() for vehicle in vehicles])


@bp.get("/vehicles/<int:id>")
def get_vehicle(id):
    vehicle = db.session.get(Vehicle, id)
    if vehicle is None:
        raise NotFound(f"vehicle {id} not found")
    return jsonify(vehicle.to_dict())


@bp.get("/customers")
def list_customers():
    customers = (
        db.session.execute(db.select(Customer).order_by(Customer.ID)).scalars()
    )
    return jsonify([customer.to_dict() for customer in customers])


@bp.get("/customers/<int:id>")
def get_customer(id):
    customer = db.session.get(Customer, id)
    if customer is None:
        raise NotFound(f"customer {id} not found")
    return jsonify(customer.to_dict())


@bp.get("/users")
def list_users():
    users = db.session.execute(db.select(AppUser).order_by(AppUser.ID_INT)).scalars()
    return jsonify([user.to_dict() for user in users])


@bp.get("/users/<int:id>")
def get_user(id):
    user = db.session.get(AppUser, id)
    if user is None:
        raise NotFound(f"user {id} not found")
    return jsonify(user.to_dict())
