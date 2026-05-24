from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from parking_app.services.payment_service import calculate_paid_until, calculate_payment_status
from parking_app.services.settings_service import DEFAULT_WARNING_DAYS


@dataclass(frozen=True)
class CardPaymentView:
    paid_until: date | None
    payment_status: str


def build_card_payment_view(
    *,
    active_period_ends: list[date],
    today: date,
    warning_days: int = DEFAULT_WARNING_DAYS,
) -> CardPaymentView:
    paid_until = calculate_paid_until(active_period_ends)
    status = calculate_payment_status(paid_until, today=today, warning_days=warning_days)
    return CardPaymentView(paid_until=paid_until, payment_status=str(status))
