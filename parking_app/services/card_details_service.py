from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle
from parking_app.services.payment_service import calculate_payment_status


@dataclass(frozen=True)
class CardDetails:
    card_id: int
    card_number: str
    paper_card_number: str | None
    card_status: str
    start_date: date
    closed_at: date | None
    attendant_name: str
    card_note: str
    closed_with_active_paid_period: bool
    refund_days: int
    refund_amount_kopecks: int
    refund_note: str
    client_fio: str
    phone: str
    document_type: str
    document_number: str
    address: str
    vehicle_title: str
    state_number: str
    color: str
    vehicle_note: str
    place_number: str
    place_status: str
    place_note: str
    paid_until: date | None
    payment_status: str


@dataclass(frozen=True)
class CardPaymentRow:
    payment_id: int
    payment_date: date
    period_from: date
    period_to: date
    amount_kopecks: int
    receipt_number: str
    fiscal_number: str
    accepted_by: str
    status: str
    note: str


def _or_dash(value: str | None) -> str:
    v = (value or "").strip()
    return v if v else "—"


def _join(parts: list[str | None]) -> str:
    joined = " ".join(p.strip() for p in parts if p and p.strip())
    return joined if joined else "—"


def get_card_details(
    session: Session,
    *,
    parking_card_id: int,
    today: date,
    warning_days: int = 3,
) -> tuple[CardDetails, list[CardPaymentRow]]:
    rec = session.execute(
        select(ParkingCard, Client, Vehicle, ParkingPlace)
        .join(Client, Client.id == ParkingCard.client_id)
        .join(Vehicle, Vehicle.id == ParkingCard.vehicle_id)
        .join(ParkingPlace, ParkingPlace.id == ParkingCard.place_id)
        .where(ParkingCard.id == parking_card_id)
    ).first()
    if rec is None:
        raise ValueError("CARD_NOT_FOUND")

    card, client, vehicle, place = rec

    paid_until = session.scalar(
        select(func.max(Payment.period_to)).where(Payment.parking_card_id == card.id, Payment.status == "active")
    )
    payment_status = calculate_payment_status(paid_until, today=today, warning_days=warning_days)

    payment_rows = session.execute(
        select(Payment)
        .where(Payment.parking_card_id == card.id)
        .order_by(Payment.payment_date.desc(), Payment.id.desc())
    ).scalars()

    payments = [
        CardPaymentRow(
            payment_id=p.id,
            payment_date=p.payment_date,
            period_from=p.period_from,
            period_to=p.period_to,
            amount_kopecks=p.amount_kopecks,
            receipt_number=_or_dash(p.receipt_number),
            fiscal_number=_or_dash(p.fiscal_number),
            accepted_by=_or_dash(p.accepted_by),
            status=p.status,
            note=_or_dash(p.note),
        )
        for p in payment_rows
    ]

    details = CardDetails(
        card_id=card.id,
        card_number=card.card_number,
        paper_card_number=card.paper_card_number,
        card_status=card.status,
        start_date=card.start_date,
        closed_at=card.closed_at,
        attendant_name=_or_dash(card.attendant_name),
        card_note=_or_dash(card.note),
        closed_with_active_paid_period=bool(card.closed_with_active_paid_period),
        refund_days=int(card.refund_days or 0),
        refund_amount_kopecks=int(card.refund_amount_kopecks or 0),
        refund_note=_or_dash(card.refund_note),
        client_fio=_join([client.surname, client.name, client.patronymic]),
        phone=_or_dash(client.phone),
        document_type=_or_dash(client.document_type),
        document_number=_or_dash(client.document_number),
        address=_or_dash(client.address),
        vehicle_title=_join([vehicle.brand, vehicle.model]),
        state_number=_or_dash(vehicle.state_number),
        color=_or_dash(vehicle.color),
        vehicle_note=_or_dash(vehicle.note),
        place_number=_or_dash(place.place_number),
        place_status=_or_dash(place.status),
        place_note=_or_dash(place.note),
        paid_until=paid_until,
        payment_status=payment_status,
    )
    return details, payments
