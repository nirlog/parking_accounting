from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from parking_app.database.models import Vehicle


def list_vehicles_for_client(session: Session, client_id: int) -> list[Vehicle]:
    stmt: Select[tuple[Vehicle]] = select(Vehicle).where(Vehicle.client_id == client_id).order_by(Vehicle.id)
    return list(session.scalars(stmt))


def get_vehicle(session: Session, vehicle_id: int) -> Vehicle | None:
    return session.get(Vehicle, vehicle_id)


def create_vehicle(
    session: Session,
    *,
    client_id: int,
    state_number: str,
    brand: str | None = None,
    model: str | None = None,
    color: str | None = None,
    photo_path: str | None = None,
    note: str | None = None,
) -> Vehicle:
    vehicle = Vehicle(
        client_id=client_id,
        state_number=state_number,
        brand=brand,
        model=model,
        color=color,
        photo_path=photo_path,
        note=note,
    )
    session.add(vehicle)
    session.flush()
    return vehicle
