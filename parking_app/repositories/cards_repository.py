from __future__ import annotations

from sqlalchemy import Select, exists, select
from sqlalchemy.orm import Session

from parking_app.database.models import ParkingCard, Vehicle


ACTIVE_CARD_STATUSES = ("active",)


def _active_cards_query() -> Select[tuple[ParkingCard]]:
    return select(ParkingCard).where(ParkingCard.status.in_(ACTIVE_CARD_STATUSES))


def has_active_card_for_place(session: Session, place_id: int) -> bool:
    stmt = select(exists(_active_cards_query().where(ParkingCard.place_id == place_id).subquery()))
    return bool(session.scalar(stmt))


def has_active_card_for_vehicle(session: Session, vehicle_id: int) -> bool:
    stmt = select(exists(_active_cards_query().where(ParkingCard.vehicle_id == vehicle_id).subquery()))
    return bool(session.scalar(stmt))



def has_active_card_for_state_number(session: Session, state_number: str) -> bool:
    stmt = select(
        exists(
            _active_cards_query()
            .join(Vehicle, Vehicle.id == ParkingCard.vehicle_id)
            .where(Vehicle.state_number == state_number)
            .subquery()
        )
    )
    return bool(session.scalar(stmt))

def card_number_exists(session: Session, card_number: str) -> bool:
    stmt = select(exists(select(ParkingCard.id).where(ParkingCard.card_number == card_number).subquery()))
    return bool(session.scalar(stmt))


def next_card_number(session: Session, width: int = 6) -> str:
    stmt = select(ParkingCard.card_number)
    max_numeric_value = 0
    for card_number in session.scalars(stmt):
        if card_number and str(card_number).isdigit():
            max_numeric_value = max(max_numeric_value, int(card_number))
    return str(max_numeric_value + 1).zfill(width)
