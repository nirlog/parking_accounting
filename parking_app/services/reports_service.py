from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class OverdueItem:
    card_id: int
    paid_until: date
    overdue_days: int


@dataclass(frozen=True)
class PaymentsPeriodSummary:
    active_count: int
    cancelled_count: int
    active_amount_kopecks: int


@dataclass(frozen=True)
class PlacesOccupancySummary:
    occupied_count: int
    free_count: int


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


def build_payments_period_summary(rows: list[dict]) -> PaymentsPeriodSummary:
    active_count = 0
    cancelled_count = 0
    active_amount_kopecks = 0

    for row in rows:
        status = str(row.get("status", "")).strip().lower()
        amount_kopecks = int(row.get("amount_kopecks") or 0)
        if status == "active":
            active_count += 1
            active_amount_kopecks += amount_kopecks
        elif status == "cancelled":
            cancelled_count += 1

    return PaymentsPeriodSummary(
        active_count=active_count,
        cancelled_count=cancelled_count,
        active_amount_kopecks=active_amount_kopecks,
    )


def build_places_occupancy_summary(rows: list[dict]) -> PlacesOccupancySummary:
    occupied_count = 0
    free_count = 0
    for row in rows:
        status = str(row.get("display_status", "")).strip().lower()
        if status == "occupied":
            occupied_count += 1
        elif status == "free":
            free_count += 1
    return PlacesOccupancySummary(occupied_count=occupied_count, free_count=free_count)
