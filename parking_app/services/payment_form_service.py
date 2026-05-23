from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from parking_app.database.models import Payment


def parse_amount_to_kopecks(raw: str) -> int:
    value = (raw or "").strip().replace(",", ".")
    if not value:
        raise ValueError("AMOUNT_REQUIRED")
    try:
        dec = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("AMOUNT_INVALID") from exc
    if dec <= 0:
        raise ValueError("AMOUNT_MUST_BE_POSITIVE")
    return int((dec * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def add_one_month_minus_one_day(start: date) -> date:
    year = start.year + (1 if start.month == 12 else 0)
    month = 1 if start.month == 12 else start.month + 1
    day = min(start.day, monthrange(year, month)[1])
    next_month_same_day = date(year, month, day)
    return next_month_same_day - timedelta(days=1)


def get_next_payment_period(session: Session, *, parking_card_id: int, card_start_date: date) -> tuple[date, date]:
    max_active_to = session.scalar(
        select(func.max(Payment.period_to)).where(Payment.parking_card_id == parking_card_id, Payment.status == "active")
    )
    period_from = (max_active_to + timedelta(days=1)) if max_active_to is not None else card_start_date
    period_to = add_one_month_minus_one_day(period_from)
    return period_from, period_to


def format_paid_until(paid_until: date | None) -> str:
    return paid_until.strftime("%d.%m.%Y") if paid_until is not None else "Нет оплат"
