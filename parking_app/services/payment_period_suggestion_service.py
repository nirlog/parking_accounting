from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import calendar


@dataclass(frozen=True)
class SuggestedPeriod:
    period_from: date
    period_to: date


def _add_one_month_minus_one_day(d: date) -> date:
    year = d.year + (1 if d.month == 12 else 0)
    month = 1 if d.month == 12 else d.month + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    next_month_same_day = date(year, month, day)
    return next_month_same_day - timedelta(days=1)


def suggest_next_payment_period(*, start_date: date, latest_paid_until: date | None) -> SuggestedPeriod:
    """Suggest next payment period according to MVP rules."""
    if latest_paid_until is None:
        period_from = start_date
    else:
        period_from = latest_paid_until + timedelta(days=1)
    period_to = _add_one_month_minus_one_day(period_from)
    return SuggestedPeriod(period_from=period_from, period_to=period_to)
