from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from parking_app.database.models import ParkingCard, ParkingPlace
from parking_app.repositories.cards_repository import (
    card_number_exists,
    has_active_card_for_place,
    has_active_card_for_state_number,
)
from parking_app.repositories.clients_repository import create_client
from parking_app.repositories.places_repository import create_place
from parking_app.repositories.vehicles_repository import create_vehicle
from parking_app.services.card_service import validate_new_card_constraints
from parking_app.services.normalization_service import normalize_phone, normalize_state_number


@dataclass(frozen=True)
class CreateCardInput:
    surname: str
    name: str
    patronymic: str | None
    phone: str | None
    document_type: str | None
    document_number: str | None
    address: str | None
    brand: str | None
    model: str | None
    color: str | None
    state_number: str
    vehicle_note: str | None
    card_number: str
    paper_card_number: str | None
    place_number: str
    start_date: date
    attendant_name: str | None
    card_note: str | None


def create_card_with_related(session: Session, payload: CreateCardInput) -> ParkingCard:
    surname = payload.surname.strip()
    name = payload.name.strip()
    state_number_raw = payload.state_number.strip()
    place_number = payload.place_number.strip()
    card_number = payload.card_number.strip()

    if not surname:
        raise ValueError("SURNAME_REQUIRED")
    if not name:
        raise ValueError("NAME_REQUIRED")
    if not state_number_raw:
        raise ValueError("STATE_NUMBER_REQUIRED")
    if not place_number:
        raise ValueError("PLACE_NUMBER_REQUIRED")
    if not card_number:
        raise ValueError("CARD_NUMBER_REQUIRED")

    normalized_state_number = normalize_state_number(state_number_raw)

    place = session.scalar(select(ParkingPlace).where(ParkingPlace.place_number == place_number))
    if place is None:
        place = create_place(session, place_number=place_number, status="free")

    validation_error = validate_new_card_constraints(
        place_has_active_card=has_active_card_for_place(session, place.id),
        vehicle_has_active_card=has_active_card_for_state_number(session, normalized_state_number),
        card_number_exists=card_number_exists(session, card_number),
    )
    if validation_error is not None:
        raise ValueError(validation_error.code)

    client = create_client(
        session,
        surname=surname,
        name=name,
        patronymic=(payload.patronymic or "").strip() or None,
        phone=normalize_phone(payload.phone or "") or None,
        document_type=(payload.document_type or "").strip() or None,
        document_number=(payload.document_number or "").strip() or None,
        address=(payload.address or "").strip() or None,
    )
    vehicle = create_vehicle(
        session,
        client_id=client.id,
        state_number=normalized_state_number,
        brand=(payload.brand or "").strip() or None,
        model=(payload.model or "").strip() or None,
        color=(payload.color or "").strip() or None,
        note=(payload.vehicle_note or "").strip() or None,
    )

    card = ParkingCard(
        card_number=card_number,
        paper_card_number=(payload.paper_card_number or "").strip() or None,
        client_id=client.id,
        vehicle_id=vehicle.id,
        place_id=place.id,
        start_date=payload.start_date,
        status="active",
        attendant_name=(payload.attendant_name or "").strip() or None,
        note=(payload.card_note or "").strip() or None,
    )
    session.add(card)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("INTEGRITY_ERROR") from exc
    return card
