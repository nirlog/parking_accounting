from __future__ import annotations

from datetime import date
from importlib.util import find_spec
import unittest

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from parking_app.database.db import Base
    from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle
    from parking_app.services.card_details_service import get_card_details


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class CardDetailsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def _create_card(self, session) -> ParkingCard:
        client = Client(surname="Иванов", name="Иван", patronymic="Иваныч")
        session.add(client)
        session.flush()
        vehicle = Vehicle(client_id=client.id, state_number="А123АА178", brand="Toyota", model="Camry")
        place = ParkingPlace(place_number="101", status="free")
        session.add_all([vehicle, place])
        session.flush()
        card = ParkingCard(
            card_number="0001",
            client_id=client.id,
            vehicle_id=vehicle.id,
            place_id=place.id,
            start_date=date(2026, 5, 1),
            status="closed",
            closed_at=date(2026, 5, 20),
            closed_with_active_paid_period=True,
            refund_days=2,
            refund_amount_kopecks=5000,
            refund_note="note",
            vehicle_state_number="А123АА178",
        )
        session.add(card)
        session.flush()
        return card

    def test_get_card_details_returns_full_data(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session)
            session.add_all([
                Payment(parking_card_id=card.id, payment_date=date(2026, 5, 2), period_from=date(2026, 5, 1), period_to=date(2026, 5, 31), amount_kopecks=100000, status="active"),
                Payment(parking_card_id=card.id, payment_date=date(2026, 6, 2), period_from=date(2026, 6, 1), period_to=date(2026, 6, 30), amount_kopecks=100000, status="cancelled"),
            ])
            session.commit()

            details, payments = get_card_details(session, parking_card_id=card.id, today=date(2026, 5, 10))
            self.assertEqual(details.client_fio, "Иванов Иван Иваныч")
            self.assertEqual(details.vehicle_title, "Toyota Camry")
            self.assertEqual(details.place_number, "101")
            self.assertEqual(details.paid_until, date(2026, 5, 31))
            self.assertEqual(len(payments), 2)
            self.assertEqual(payments[0].status, "cancelled")
            self.assertEqual(details.closed_at, date(2026, 5, 20))
            self.assertEqual(details.refund_amount_kopecks, 5000)

    def test_missing_card(self) -> None:
        with self.SessionLocal() as session:
            with self.assertRaisesRegex(ValueError, "CARD_NOT_FOUND"):
                get_card_details(session, parking_card_id=999, today=date.today())

    def test_empty_fields_are_dash(self) -> None:
        with self.SessionLocal() as session:
            client = Client(surname="Иванов", name="Иван")
            session.add(client)
            session.flush()
            vehicle = Vehicle(client_id=client.id, state_number="А123АА178")
            place = ParkingPlace(place_number="1", status="free")
            session.add_all([vehicle, place])
            session.flush()
            card = ParkingCard(card_number="1", client_id=client.id, vehicle_id=vehicle.id, place_id=place.id, start_date=date.today(), status="active", vehicle_state_number="А123АА178")
            session.add(card)
            session.commit()
            details, _ = get_card_details(session, parking_card_id=card.id, today=date.today())
            self.assertEqual(details.address, "—")
            self.assertEqual(details.vehicle_note, "—")

if __name__ == "__main__":
    unittest.main()
