from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Select, exists, select
from sqlalchemy.orm import Session

from parking_app.database.models import ParkingCard, Payment


ACTIVE_PAYMENT_STATUSES = ("active",)


def _active_payments_for_card_query(parking_card_id: int) -> Select[tuple[Payment]]:
    return select(Payment).where(
        Payment.parking_card_id == parking_card_id,
        Payment.status.in_(ACTIVE_PAYMENT_STATUSES),
    )


def has_overlap_with_active_periods(
    session: Session,
    *,
    parking_card_id: int,
    period_from: date,
    period_to: date,
) -> bool:
    """Return True when a new period intersects an active payment period.

    Intersection rule:
      new_from <= existing_to AND new_to >= existing_from
    """
    active_stmt = _active_payments_for_card_query(parking_card_id).where(
        period_from <= Payment.period_to,
        period_to >= Payment.period_from,
    )
    stmt = select(exists(active_stmt.subquery()))
    return bool(session.scalar(stmt))


def create_payment(
    session: Session,
    *,
    parking_card_id: int,
    payment_date: date,
    period_from: date,
    period_to: date,
    amount_kopecks: int,
    receipt_number: str | None = None,
    fiscal_number: str | None = None,
    accepted_by: str | None = None,
    note: str | None = None,
 ) -> Payment:
    card = session.get(ParkingCard, parking_card_id)
    if card is None:
        raise ValueError("PAYMENT_CARD_NOT_FOUND")
    if card.status != "active":
        raise ValueError("PAYMENT_CARD_NOT_ACTIVE")

    if has_overlap_with_active_periods(
        session,
        parking_card_id=parking_card_id,
        period_from=period_from,
        period_to=period_to,
    ):
        raise ValueError("PAYMENT_PERIOD_OVERLAP")

    payment = Payment(
        parking_card_id=parking_card_id,
        payment_date=payment_date,
        period_from=period_from,
        period_to=period_to,
        amount_kopecks=amount_kopecks,
        receipt_number=receipt_number,
        fiscal_number=fiscal_number,
        accepted_by=accepted_by,
        note=note,
        status="active",
    )
    session.add(payment)
    session.flush()
    return payment


def cancel_payment(
    session: Session,
    *,
    payment_id: int,
    cancel_reason: str,
    cancelled_at: datetime,
) -> Payment | None:
    payment = session.get(Payment, payment_id)
    if payment is None:
        return None
    if payment.status != "active":
        return payment
    payment.status = "cancelled"
    payment.cancel_reason = cancel_reason
    payment.cancelled_at = cancelled_at
    session.flush()
    return payment
