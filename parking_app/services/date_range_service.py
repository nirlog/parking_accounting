from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import calendar


@dataclass(frozen=True)
class DateRange:
    date_from: date
    date_to: date


def today_range(today: date) -> DateRange:
    return DateRange(date_from=today, date_to=today)


def month_range(today: date) -> DateRange:
    first = date(today.year, today.month, 1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    last = date(today.year, today.month, last_day)
    return DateRange(date_from=first, date_to=last)


def validate_custom_range(date_from: date, date_to: date) -> bool:
    return date_from <= date_to
