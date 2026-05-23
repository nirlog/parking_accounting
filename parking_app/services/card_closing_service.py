from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from parking_app.services.payment_service import calculate_refund


@dataclass(frozen=True)
class CloseCardResult:
    closed_with_active_paid_period: bool
    refund_days: int
    refund_amount_kopecks: int


def calculate_close_card_result(
    *,
    closed_at: date,
    paid_period_from: date | None,
    paid_period_to: date | None,
    paid_amount_kopecks: int | None,
) -> CloseCardResult:
    """Calculate closing flags and refund data for a card.

    If no active payment exists, returns zero refund and closed_with_active_paid_period=False.
    """
    if not paid_period_from or not paid_period_to or not paid_amount_kopecks:
        return CloseCardResult(False, 0, 0)

    refund_days, refund_amount = calculate_refund(
        period_from=paid_period_from,
        period_to=paid_period_to,
        amount_kopecks=paid_amount_kopecks,
        closed_at=closed_at,
    )

    return CloseCardResult(
        closed_with_active_paid_period=refund_days > 0,
        refund_days=refund_days,
        refund_amount_kopecks=refund_amount,
    )
