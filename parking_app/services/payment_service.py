from __future__ import annotations

from datetime import date

from parking_app.app.constants import PaymentStatus


def calculate_paid_until(active_period_ends: list[date]) -> date | None:
    """Return the latest paid-until date from active payments or None."""
    return max(active_period_ends) if active_period_ends else None


def calculate_payment_status(
    paid_until: date | None,
    *,
    today: date,
    warning_days: int = 3,
) -> PaymentStatus:
    """Return mutually exclusive payment status according to spec.

    Rules:
    - None paid_until => NO_PAYMENTS
    - paid_until < today => OVERDUE
    - today <= paid_until <= today + warning_days => EXPIRING_SOON
    - paid_until > today + warning_days => PAID
    """
    if paid_until is None:
        return PaymentStatus.NO_PAYMENTS

    if paid_until < today:
        return PaymentStatus.OVERDUE

    border = today.toordinal() + max(0, warning_days)
    if paid_until.toordinal() <= border:
        return PaymentStatus.EXPIRING_SOON

    return PaymentStatus.PAID
