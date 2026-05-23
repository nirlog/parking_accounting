from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from parking_app.database.models import Payment
from parking_app.repositories.payments_repository import cancel_payment


def cancel_active_payment(
    session: Session,
    *,
    payment_id: int,
    cancel_reason: str,
    cancelled_at: datetime,
) -> Payment:
    payment = session.get(Payment, payment_id)
    if payment is None:
        raise ValueError("PAYMENT_NOT_FOUND")
    if payment.status != "active":
        raise ValueError("PAYMENT_NOT_ACTIVE")

    normalized_reason = cancel_reason.strip()
    if not normalized_reason:
        raise ValueError("PAYMENT_CANCEL_REASON_REQUIRED")

    cancelled = cancel_payment(
        session,
        payment_id=payment_id,
        cancel_reason=normalized_reason,
        cancelled_at=cancelled_at,
    )
    # Defensive: repository returns None only when payment is missing.
    if cancelled is None:
        raise ValueError("PAYMENT_NOT_FOUND")
    session.flush()
    return cancelled
