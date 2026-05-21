from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class OverdueItem:
    card_id: int
    paid_until: date
    overdue_days: int


def calculate_overdue_days(*, paid_until: date, today: date) -> int:
    """Return overdue days. If not overdue, returns 0."""
    if paid_until >= today:
        return 0
    return (today - paid_until).days


def build_overdue_items(rows: list[dict], *, today: date) -> list[OverdueItem]:
    """Build overdue report rows from card/payment projection rows.

    Expected row keys:
    - card_id: int
    - paid_until: date | None
    - payment_status: str
    """
    result: list[OverdueItem] = []
    for row in rows:
        status = row.get("payment_status")
        paid_until = row.get("paid_until")
        if status != "Просрочено" or paid_until is None:
            continue
        result.append(
            OverdueItem(
                card_id=int(row["card_id"]),
                paid_until=paid_until,
                overdue_days=calculate_overdue_days(paid_until=paid_until, today=today),
            )
        )
    return result
