from __future__ import annotations

from datetime import date

from sqlalchemy import Select, exists, select
from sqlalchemy.orm import Session

from parking_app.database.models import Payment


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
