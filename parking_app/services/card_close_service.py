from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from parking_app.database.models import ParkingCard, Payment
from parking_app.services.card_closing_service import CloseCardResult
from parking_app.services.payment_service import calculate_refund


def calculate_refund_for_active_payments(
    payments: list[Payment],
    *,
    closed_at: date,
) -> CloseCardResult:
    total_refund_days = 0
    total_refund_amount_kopecks = 0
    for payment in payments:
        refund_days, refund_amount = calculate_refund(
            period_from=payment.period_from,
            period_to=payment.period_to,
            amount_kopecks=payment.amount_kopecks,
            closed_at=closed_at,
        )
        total_refund_days += refund_days
        total_refund_amount_kopecks += refund_amount

    return CloseCardResult(
        closed_with_active_paid_period=total_refund_days > 0,
        refund_days=total_refund_days,
        refund_amount_kopecks=total_refund_amount_kopecks,
    )


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

    payments = list(
        session.execute(
            select(Payment)
            .where(
                Payment.parking_card_id == parking_card_id,
                Payment.status == "active",
                Payment.period_to > closed_at,
            )
            .order_by(Payment.period_from.asc(), Payment.period_to.asc(), Payment.id.asc())
        ).scalars()
    )
    result = calculate_refund_for_active_payments(payments, closed_at=closed_at)

    card.status = "closed"
    card.closed_at = closed_at
    card.closed_with_active_paid_period = result.closed_with_active_paid_period
    card.refund_days = result.refund_days
    card.refund_amount_kopecks = result.refund_amount_kopecks
    card.refund_note = refund_note

    session.flush()
    return card
