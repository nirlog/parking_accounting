from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from parking_app.database.models import ParkingCard, Payment
from parking_app.services.card_closing_service import calculate_close_card_result


def close_active_card(
    session: Session,
    *,
    parking_card_id: int,
    closed_at: date,
    refund_note: str | None = None,
) -> ParkingCard:
    card = session.get(ParkingCard, parking_card_id)
    if card is None:
        raise ValueError("CARD_NOT_FOUND")
    if card.status != "active":
        raise ValueError("CARD_NOT_ACTIVE")

    last_payment = session.execute(
        select(Payment)
        .where(Payment.parking_card_id == parking_card_id, Payment.status == "active")
        .order_by(Payment.period_to.desc(), Payment.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    result = calculate_close_card_result(
        closed_at=closed_at,
        paid_period_from=last_payment.period_from if last_payment is not None else None,
        paid_period_to=last_payment.period_to if last_payment is not None else None,
        paid_amount_kopecks=last_payment.amount_kopecks if last_payment is not None else None,
    )

    card.status = "closed"
    card.closed_at = closed_at
    card.closed_with_active_paid_period = result.closed_with_active_paid_period
    card.refund_days = result.refund_days
    card.refund_amount_kopecks = result.refund_amount_kopecks
    card.refund_note = refund_note

    session.flush()
    return card
