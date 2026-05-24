from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle
from parking_app.services.normalization_service import normalize_state_number
from parking_app.services.payment_service import calculate_payment_status


@dataclass(frozen=True)
class PlaceTableRow:
    place_id: int
    place_number: str
    base_status: str
    display_status: str
    client_fio: str
    state_number: str
    vehicle: str
    paid_until: date | None
    payment_status: str
    note: str


def _compact_join(parts: list[str | None]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def _natural_place_key(place_number: str) -> tuple[int, int | str]:
    value = place_number.strip()
    if value.isdigit():
        return (0, int(value))
    return (1, value)


def _active_payment_until_by_card(session: Session) -> dict[int, date]:
    stmt = (
        select(Payment.parking_card_id, func.max(Payment.period_to).label("paid_until"))
        .where(Payment.status == "active")
        .group_by(Payment.parking_card_id)
    )
    result: dict[int, date] = {}
    for rec in session.execute(stmt):
        if rec.paid_until is not None:
            result[int(rec.parking_card_id)] = rec.paid_until
    return result


def build_place_table_rows(
    session: Session,
    *,
    today: date,
    warning_days: int = 3,
) -> list[PlaceTableRow]:
    paid_until_by_card = _active_payment_until_by_card(session)

    stmt: Select = (
        select(
            ParkingPlace.id.label("place_id"),
            ParkingPlace.place_number,
            ParkingPlace.status.label("base_status"),
            ParkingPlace.note.label("place_note"),
            ParkingCard.id.label("card_id"),
            Client.surname,
            Client.name,
            Client.patronymic,
            Vehicle.state_number,
            Vehicle.brand,
            Vehicle.model,
        )
        .select_from(ParkingPlace)
        .outerjoin(
            ParkingCard,
            (ParkingCard.place_id == ParkingPlace.id) & (ParkingCard.status == "active"),
        )
        .outerjoin(Client, Client.id == ParkingCard.client_id)
        .outerjoin(Vehicle, Vehicle.id == ParkingCard.vehicle_id)
    )

    rows: list[PlaceTableRow] = []
    for rec in session.execute(stmt):
        note = rec.place_note.strip() if isinstance(rec.place_note, str) and rec.place_note.strip() else "—"

        if rec.card_id is not None:
            paid_until = paid_until_by_card.get(int(rec.card_id))
            payment_status = str(calculate_payment_status(paid_until, today=today, warning_days=warning_days))
            rows.append(
                PlaceTableRow(
                    place_id=int(rec.place_id),
                    place_number=rec.place_number,
                    base_status=rec.base_status,
                    display_status="occupied",
                    client_fio=_compact_join([rec.surname, rec.name, rec.patronymic]) or "—",
                    state_number=rec.state_number or "—",
                    vehicle=_compact_join([rec.brand, rec.model]) or "—",
                    paid_until=paid_until,
                    payment_status=payment_status,
                    note=note,
                )
            )
        else:
            rows.append(
                PlaceTableRow(
                    place_id=int(rec.place_id),
                    place_number=rec.place_number,
                    base_status=rec.base_status,
                    display_status=rec.base_status,
                    client_fio="—",
                    state_number="—",
                    vehicle="—",
                    paid_until=None,
                    payment_status="—",
                    note=note,
                )
            )

    return sorted(rows, key=lambda r: (_natural_place_key(r.place_number), r.place_id))


def filter_place_rows(rows: list[PlaceTableRow], filter_name: str) -> list[PlaceTableRow]:
    if filter_name == "Все места":
        return rows
    if filter_name == "Свободные":
        return [r for r in rows if r.display_status == "free"]
    if filter_name == "Занятые":
        return [r for r in rows if r.display_status == "occupied"]
    if filter_name == "Просроченные":
        return [r for r in rows if r.display_status == "occupied" and r.payment_status == "Просрочено"]
    if filter_name == "Оплата скоро закончится":
        return [r for r in rows if r.display_status == "occupied" and r.payment_status == "Скоро закончится"]
    if filter_name == "Нет оплат":
        return [r for r in rows if r.display_status == "occupied" and r.payment_status == "Нет оплат"]
    if filter_name == "Бронь":
        return [r for r in rows if r.display_status == "reserved"]
    if filter_name == "Ремонт":
        return [r for r in rows if r.display_status == "repair"]
    return rows


def filter_place_rows_by_search(rows: list[PlaceTableRow], query: str) -> list[PlaceTableRow]:
    q = query.strip()
    if not q:
        return rows

    q_lower = q.lower()
    q_plate = normalize_state_number(q)

    result: list[PlaceTableRow] = []
    for row in rows:
        haystack = " ".join([
            row.place_number.lower(),
            row.client_fio.lower(),
            row.state_number.lower(),
            row.vehicle.lower(),
            row.note.lower(),
        ])
        matched = q_lower in haystack
        if not matched and q_plate:
            matched = q_plate in normalize_state_number(row.state_number)
        if matched:
            result.append(row)
    return result
