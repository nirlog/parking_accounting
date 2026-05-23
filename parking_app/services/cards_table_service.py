from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle
from parking_app.services.normalization_service import normalize_phone, normalize_state_number
from parking_app.services.payment_service import calculate_payment_status


@dataclass(frozen=True)
class CardTableRow:
    card_id: int
    card_number: str
    paper_card_number: str | None
    place_number: str
    fio: str
    state_number: str
    vehicle: str
    phone: str
    paid_until: date | None
    payment_status: str
    card_status: str


def _compact_join(parts: list[str | None]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def build_card_table_rows(session: Session, *, today: date, warning_days: int = 3) -> list[CardTableRow]:
    paid_until_subq = (
        select(Payment.parking_card_id, func.max(Payment.period_to).label("paid_until"))
        .where(Payment.status == "active")
        .group_by(Payment.parking_card_id)
        .subquery()
    )

    stmt: Select = (
        select(
            ParkingCard.id,
            ParkingCard.status,
            ParkingCard.card_number,
            ParkingCard.paper_card_number,
            ParkingPlace.place_number,
            Client.surname,
            Client.name,
            Client.patronymic,
            Client.phone,
            Vehicle.state_number,
            Vehicle.brand,
            Vehicle.model,
            paid_until_subq.c.paid_until,
        )
        .join(ParkingPlace, ParkingPlace.id == ParkingCard.place_id)
        .join(Client, Client.id == ParkingCard.client_id)
        .join(Vehicle, Vehicle.id == ParkingCard.vehicle_id)
        .outerjoin(paid_until_subq, paid_until_subq.c.parking_card_id == ParkingCard.id)
    )

    rows: list[CardTableRow] = []
    for rec in session.execute(stmt):
        fio = _compact_join([rec.surname, rec.name, rec.patronymic])
        vehicle = _compact_join([rec.brand, rec.model]) or "—"
        phone = rec.phone.strip() if isinstance(rec.phone, str) and rec.phone.strip() else "—"
        paid_until = rec.paid_until
        payment_status = str(calculate_payment_status(paid_until, today=today, warning_days=warning_days))

        rows.append(
            CardTableRow(
                card_id=rec.id,
                card_number=rec.card_number,
                paper_card_number=rec.paper_card_number or None,
                place_number=rec.place_number,
                fio=fio,
                state_number=rec.state_number,
                vehicle=vehicle,
                phone=phone,
                paid_until=paid_until,
                payment_status=payment_status,
                card_status=rec.status,
            )
        )

    def status_rank(status: str) -> int:
        return 0 if status == "active" else 1

    def place_sort_key(place_number: str) -> tuple[int, int | str]:
        value = place_number.strip()
        if value.isdigit():
            return (0, int(value))
        return (1, value)

    return sorted(rows, key=lambda r: (status_rank(r.card_status), place_sort_key(r.place_number), r.card_id))


def filter_rows_by_quick_filter(rows: list[CardTableRow], filter_name: str) -> list[CardTableRow]:
    if filter_name == "Все активные":
        return [r for r in rows if r.card_status == "active"]
    if filter_name == "Просроченные":
        return [r for r in rows if r.card_status == "active" and r.payment_status == "Просрочено"]
    if filter_name == "Оплата скоро закончится":
        return [r for r in rows if r.card_status == "active" and r.payment_status == "Скоро закончится"]
    if filter_name == "Нет оплат":
        return [r for r in rows if r.card_status == "active" and r.payment_status == "Нет оплат"]
    if filter_name == "Закрытые":
        return [r for r in rows if r.card_status == "closed"]
    if filter_name == "Архив":
        return [r for r in rows if r.card_status == "archived"]
    return rows


def filter_rows_by_search(rows: list[CardTableRow], query: str) -> list[CardTableRow]:
    q = query.strip()
    if not q:
        return rows

    q_lower = q.lower()
    q_digits = normalize_phone(q)
    q_plate = normalize_state_number(q)

    result: list[CardTableRow] = []
    for row in rows:
        fio = row.fio.lower()
        place = row.place_number.lower()
        phone_digits = normalize_phone(row.phone)
        plate_normalized = normalize_state_number(row.state_number)
        haystack = [
            fio,
            place,
            row.phone.lower(),
            row.state_number.lower(),
            row.card_number.lower(),
            (row.paper_card_number or "").lower(),
        ]

        matched = q_lower in " ".join(haystack)
        if not matched and q_digits:
            matched = q_digits in phone_digits
        if not matched and q_plate:
            matched = q_plate in plate_normalized
        if matched:
            result.append(row)
    return result
