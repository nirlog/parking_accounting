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
    """Return mutually exclusive payment status according to spec."""
    if paid_until is None:
        return PaymentStatus.NO_PAYMENTS

    if paid_until < today:
        return PaymentStatus.OVERDUE

    border = today.toordinal() + max(0, warning_days)
    if paid_until.toordinal() <= border:
        return PaymentStatus.EXPIRING_SOON

    return PaymentStatus.PAID


def periods_overlap(
    *,
    new_period_from: date,
    new_period_to: date,
    existing_period_from: date,
    existing_period_to: date,
) -> bool:
    """Check overlap by canonical rule from the technical specification."""
    return new_period_from <= existing_period_to and new_period_to >= existing_period_from
