from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle


@dataclass(slots=True)
class DemoLoadResult:
    clients_created: int = 0
    vehicles_created: int = 0
    places_created: int = 0
    cards_created: int = 0
    payments_created: int = 0
    skipped_existing_cards: int = 0


_REL_DATE = re.compile(r"^today(?:(?P<sign>[+-])(?P<days>\d+))?$")


def _parse_relative_date(raw: str, *, today: date) -> date:
    raw = raw.strip()
    m = _REL_DATE.match(raw)
    if not m:
        return date.fromisoformat(raw)
    sign = m.group("sign")
    days = int(m.group("days") or "0")
    if sign == "+":
        return today.fromordinal(today.toordinal() + days)
    if sign == "-":
        return today.fromordinal(today.toordinal() - days)
    return today


def _is_demo_client(client: Client) -> bool:
    return bool((client.document_number or "").startswith("DEMO-"))


def _reset_existing_demo(session: Session) -> None:
    demo_cards = session.scalars(select(ParkingCard).where(ParkingCard.card_number.like("DEMO-%"))).all()
    demo_card_ids = [c.id for c in demo_cards]
    demo_vehicle_ids = [c.vehicle_id for c in demo_cards]
    demo_client_ids = [c.client_id for c in demo_cards]

    if demo_card_ids:
        session.query(Payment).filter(Payment.parking_card_id.in_(demo_card_ids)).delete(synchronize_session=False)
        session.query(ParkingCard).filter(ParkingCard.id.in_(demo_card_ids)).delete(synchronize_session=False)

    session.query(Vehicle).filter(Vehicle.note.like("%[demo]%")).delete(synchronize_session=False)
    session.query(ParkingPlace).filter(ParkingPlace.note.like("%[demo]%")).delete(synchronize_session=False)

    if demo_client_ids:
        clients = session.scalars(select(Client).where(Client.id.in_(demo_client_ids))).all()
        for client in clients:
            if _is_demo_client(client):
                session.delete(client)


def load_demo_data(
    session: Session,
    *,
    data_path: Path,
    reset_existing_demo: bool = False,
    today: date | None = None,
) -> DemoLoadResult:
    ref_today = today or date.today()
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    result = DemoLoadResult()

    if reset_existing_demo:
        _reset_existing_demo(session)
        session.flush()

    clients_by_key: dict[str, Client] = {}
    for item in payload["clients"]:
        key = item["key"]
        doc = item.get("document_number")
        existing = None
        if doc:
            existing = session.scalar(select(Client).where(Client.document_number == doc))
        if existing is None:
            existing = Client(
                surname=item["surname"],
                name=item["name"],
                patronymic=item.get("patronymic"),
                phone=item.get("phone"),
                document_type=item.get("document_type"),
                document_number=doc,
                address=item.get("address"),
                photo_path=None,
            )
            session.add(existing)
            session.flush()
            result.clients_created += 1
        clients_by_key[key] = existing

    places_by_number: dict[str, ParkingPlace] = {}
    for item in payload["places"]:
        number = item["place_number"]
        existing = session.scalar(select(ParkingPlace).where(ParkingPlace.place_number == number))
        if existing is None:
            existing = ParkingPlace(place_number=number, status=item.get("status", "free"), note=item.get("note"))
            session.add(existing)
            session.flush()
            result.places_created += 1
        else:
            existing.status = item.get("status", existing.status)
            existing.note = item.get("note", existing.note)
        places_by_number[number] = existing

    vehicles_by_key: dict[str, Vehicle] = {}
    for item in payload["vehicles"]:
        key = item["key"]
        existing = session.scalar(select(Vehicle).where(Vehicle.state_number == item["state_number"]))
        if existing is None:
            existing = Vehicle(
                client_id=clients_by_key[item["client_key"]].id,
                state_number=item["state_number"],
                brand=item.get("brand"),
                model=item.get("model"),
                color=item.get("color"),
                note=item.get("note"),
                photo_path=None,
            )
            session.add(existing)
            session.flush()
            result.vehicles_created += 1
        vehicles_by_key[key] = existing

    for card in payload["cards"]:
        card_number = card["card_number"]
        existing = session.scalar(select(ParkingCard).where(ParkingCard.card_number == card_number))
        if existing is not None:
            result.skipped_existing_cards += 1
            continue

        vehicle = vehicles_by_key[card["vehicle_key"]]
        parking_card = ParkingCard(
            card_number=card_number,
            paper_card_number=card.get("paper_card_number"),
            client_id=clients_by_key[card["client_key"]].id,
            vehicle_id=vehicle.id,
            place_id=places_by_number[card["place_number"]].id,
            start_date=_parse_relative_date(card["start_date"], today=ref_today),
            closed_at=_parse_relative_date(card["closed_at"], today=ref_today) if card.get("closed_at") else None,
            status=card["status"],
            vehicle_state_number=vehicle.state_number if card["status"] == "active" else None,
            attendant_name=card.get("attendant_name"),
            note=card.get("note"),
        )
        session.add(parking_card)
        session.flush()
        result.cards_created += 1

        for payment in card.get("payments", []):
            p = Payment(
                parking_card_id=parking_card.id,
                payment_date=_parse_relative_date(payment["payment_date"], today=ref_today),
                period_from=_parse_relative_date(payment["period_from"], today=ref_today),
                period_to=_parse_relative_date(payment["period_to"], today=ref_today),
                amount_kopecks=int(payment["amount_kopecks"]),
                receipt_number=payment.get("receipt_number"),
                fiscal_number=payment.get("fiscal_number"),
                accepted_by=payment.get("accepted_by"),
                status=payment.get("status", "active"),
                cancel_reason=payment.get("cancel_reason"),
                cancelled_at=datetime.now(UTC) if payment.get("status") == "cancelled" else None,
                note=payment.get("note"),
            )
            session.add(p)
            result.payments_created += 1

    return result
