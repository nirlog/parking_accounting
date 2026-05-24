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


def filter_payments(
    rows: list[dict],
    *,
    query: str = "",
    place_number: str = "",
    state_number: str = "",
    accepted_by: str = "",
    status: str = "",
) -> list[dict]:
    q = query.strip().lower()
    place_q = place_number.strip().lower()
    plate_q = state_number.strip().lower()
    accepted_q = accepted_by.strip().lower()
    status_q = status.strip().lower()

    result: list[dict] = []
    for row in rows:
        if q:
            haystack = " ".join(
                str(row.get(key, "") or "").lower()
                for key in ("fio", "state_number", "place_number", "accepted_by", "receipt_number", "fiscal_number")
            )
            if q not in haystack:
                continue
        if place_q and place_q != str(row.get("place_number", "")).lower():
            continue
        if plate_q and plate_q not in str(row.get("state_number", "")).lower():
            continue
        if accepted_q and accepted_q not in str(row.get("accepted_by", "")).lower():
            continue
        if status_q and status_q != str(row.get("status", "")).lower():
            continue
        result.append(row)
    return result
