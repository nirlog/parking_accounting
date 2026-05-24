from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from sqlalchemy import func, select

from parking_app.database.db import SessionLocal
from parking_app.database.init_db import init_db
from parking_app.database.models import ParkingCard, Payment
from parking_app.services.demo_data_service import load_demo_data


class DemoDataServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        init_db()
        self.path = Path("demo/demo_data.json")

    def test_load_demo_data_creates_entities(self) -> None:
        with SessionLocal() as session:
            result = load_demo_data(session, data_path=self.path, reset_existing_demo=True, today=date(2026, 5, 24))
            session.commit()
            self.assertGreaterEqual(result.cards_created, 10)
            self.assertGreater(result.clients_created, 0)
            self.assertGreater(result.vehicles_created, 0)
            self.assertGreater(result.places_created, 0)
            self.assertGreater(result.payments_created, 0)

    def test_repeat_without_reset_is_idempotent(self) -> None:
        with SessionLocal() as session:
            first = load_demo_data(session, data_path=self.path, reset_existing_demo=True, today=date(2026, 5, 24))
            session.commit()
            second = load_demo_data(session, data_path=self.path, reset_existing_demo=False, today=date(2026, 5, 24))
            session.commit()
            self.assertEqual(second.cards_created, 0)
            self.assertGreaterEqual(second.skipped_existing_cards, first.cards_created)

    def test_reset_recreates_demo_set(self) -> None:
        with SessionLocal() as session:
            load_demo_data(session, data_path=self.path, reset_existing_demo=True, today=date(2026, 5, 24))
            session.commit()
            cards_before = session.scalar(
                select(func.count()).select_from(ParkingCard).where(ParkingCard.card_number.like("DEMO-%"))
            )
            load_demo_data(session, data_path=self.path, reset_existing_demo=True, today=date(2026, 5, 24))
            session.commit()
            cards_after = session.scalar(
                select(func.count()).select_from(ParkingCard).where(ParkingCard.card_number.like("DEMO-%"))
            )
            self.assertEqual(cards_before, cards_after)

    def test_relative_dates_and_status_coverage(self) -> None:
        with SessionLocal() as session:
            load_demo_data(session, data_path=self.path, reset_existing_demo=True, today=date(2026, 5, 24))
            session.commit()
            cards = session.scalars(select(ParkingCard).where(ParkingCard.card_number.like("DEMO-%"))).all()
            payments = session.scalars(select(Payment).join(ParkingCard, ParkingCard.id == Payment.parking_card_id).where(ParkingCard.card_number.like("DEMO-%"))).all()

            statuses = {c.status for c in cards}
            self.assertIn("active", statuses)
            self.assertIn("closed", statuses)
            self.assertIn("archived", statuses)

            payment_statuses = {p.status for p in payments}
            self.assertIn("active", payment_statuses)
            self.assertIn("cancelled", payment_statuses)

            active_cards = [c for c in cards if c.status == "active"]
            self.assertTrue(all(c.vehicle_state_number for c in active_cards))


if __name__ == "__main__":
    unittest.main()
