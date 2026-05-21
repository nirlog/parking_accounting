from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from parking_app.database.models import ParkingPlace


def list_places(session: Session) -> list[ParkingPlace]:
    stmt: Select[tuple[ParkingPlace]] = select(ParkingPlace).order_by(ParkingPlace.place_number)
    return list(session.scalars(stmt))


def get_place(session: Session, place_id: int) -> ParkingPlace | None:
    return session.get(ParkingPlace, place_id)


def create_place(
    session: Session,
    *,
    place_number: str,
    status: str = "free",
    note: str | None = None,
) -> ParkingPlace:
    place = ParkingPlace(place_number=place_number, status=status, note=note)
    session.add(place)
    session.flush()
    return place
