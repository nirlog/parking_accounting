from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle


@dataclass(frozen=True)
class PaymentTableRow:
    payment_id: int
    payment_date: date
    period_from: date
    period_to: date
    amount_kopecks: int
    fio: str
    state_number: str
    place_number: str
    receipt_number: str
    fiscal_number: str
    accepted_by: str
    status: str
    note: str


@dataclass(frozen=True)
class PaymentFooterSummary:
    total_rows: int
    active_count: int
    cancelled_count: int
    active_amount_kopecks: int


def _compact_join(parts: list[str | None]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def _or_dash(value: str | None) -> str:
    cleaned = (value or "").strip()
    return cleaned if cleaned else "—"


def build_payment_table_rows(
    session: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    include_cancelled: bool = False,
) -> list[PaymentTableRow]:
    stmt: Select = (
        select(
            Payment.id,
            Payment.payment_date,
            Payment.period_from,
            Payment.period_to,
            Payment.amount_kopecks,
            Payment.receipt_number,
            Payment.fiscal_number,
            Payment.accepted_by,
            Payment.status,
            Payment.note,
            Client.surname,
            Client.name,
            Client.patronymic,
            Vehicle.state_number,
            ParkingPlace.place_number,
        )
        .join(ParkingCard, ParkingCard.id == Payment.parking_card_id)
        .join(Client, Client.id == ParkingCard.client_id)
        .join(Vehicle, Vehicle.id == ParkingCard.vehicle_id)
        .join(ParkingPlace, ParkingPlace.id == ParkingCard.place_id)
    )

    if include_cancelled:
        stmt = stmt.where(Payment.status.in_(("active", "cancelled")))
    else:
        stmt = stmt.where(Payment.status == "active")
    if date_from is not None:
        stmt = stmt.where(Payment.payment_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Payment.payment_date <= date_to)

    stmt = stmt.order_by(Payment.payment_date.desc(), Payment.id.desc())

    rows: list[PaymentTableRow] = []
    for rec in session.execute(stmt):
        rows.append(
            PaymentTableRow(
                payment_id=rec.id,
                payment_date=rec.payment_date,
                period_from=rec.period_from,
                period_to=rec.period_to,
                amount_kopecks=rec.amount_kopecks,
                fio=_or_dash(_compact_join([rec.surname, rec.name, rec.patronymic])),
                state_number=_or_dash(rec.state_number),
                place_number=_or_dash(rec.place_number),
                receipt_number=_or_dash(rec.receipt_number),
                fiscal_number=_or_dash(rec.fiscal_number),
                accepted_by=_or_dash(rec.accepted_by),
                status=rec.status,
                note=_or_dash(rec.note),
            )
        )
    return rows


def format_amount_kopecks(amount_kopecks: int) -> str:
    rub = amount_kopecks / 100
    return f"{rub:,.2f}".replace(",", " ")


def calculate_total_amount_kopecks(rows: list[PaymentTableRow]) -> int:
    return sum(r.amount_kopecks for r in rows if r.status == "active")


def build_payment_footer_summary(rows: list[PaymentTableRow]) -> PaymentFooterSummary:
    active_count = sum(1 for r in rows if r.status == "active")
    cancelled_count = sum(1 for r in rows if r.status == "cancelled")
    return PaymentFooterSummary(
        total_rows=len(rows),
        active_count=active_count,
        cancelled_count=cancelled_count,
        active_amount_kopecks=calculate_total_amount_kopecks(rows),
    )
