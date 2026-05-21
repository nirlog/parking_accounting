from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PaymentsSummary:
    active_count: int
    cancelled_count: int
    active_amount_kopecks: int


def calculate_payments_summary(rows: list[dict]) -> PaymentsSummary:
    active_count = 0
    cancelled_count = 0
    active_amount = 0

    for row in rows:
        status = row.get("status")
        amount = int(row.get("amount_kopecks", 0) or 0)
        if status == "active":
            active_count += 1
            active_amount += amount
        elif status == "cancelled":
            cancelled_count += 1

    return PaymentsSummary(
        active_count=active_count,
        cancelled_count=cancelled_count,
        active_amount_kopecks=active_amount,
    )


def filter_payments_by_period(rows: list[dict], *, date_from: date, date_to: date) -> list[dict]:
    return [
        row
        for row in rows
        if (payment_date := row.get("payment_date")) is not None and date_from <= payment_date <= date_to
    ]
