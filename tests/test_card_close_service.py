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
    from parking_app.services.card_close_service import close_active_card


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class CardCloseServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def _create_active_card(self, session, *, place_number: str = "101") -> ParkingCard:
        client = Client(surname="Иванов", name="Иван")
        session.add(client)
        session.flush()
        vehicle = Vehicle(client_id=client.id, state_number="А123АА178")
        session.add(vehicle)
        place = ParkingPlace(place_number=place_number, status="free")
        session.add(place)
        session.flush()
        card = ParkingCard(
            card_number=f"C-{place_number}",
            client_id=client.id,
            vehicle_id=vehicle.id,
            place_id=place.id,
            start_date=date(2026, 1, 1),
            status="active",
            vehicle_state_number="А123АА178",
        )
        session.add(card)
        session.flush()
        return card

    def test_close_active_card_without_payments(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_active_card(session)
            close_active_card(session, parking_card_id=card.id, closed_at=date(2026, 5, 21))
            session.commit()
            session.refresh(card)
            self.assertEqual(card.status, "closed")
            self.assertEqual(card.closed_at, date(2026, 5, 21))
            self.assertFalse(card.closed_with_active_paid_period)
            self.assertEqual(card.refund_days, 0)
            self.assertEqual(card.refund_amount_kopecks, 0)

    def test_close_active_card_with_future_paid_until_calculates_refund(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_active_card(session)
            session.add(
                Payment(
                    parking_card_id=card.id,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=310000,
                    status="active",
                )
            )
            session.flush()

            close_active_card(session, parking_card_id=card.id, closed_at=date(2026, 5, 21))
            session.commit()
            session.refresh(card)
            self.assertTrue(card.closed_with_active_paid_period)
            self.assertGreater(card.refund_days, 0)
            self.assertGreater(card.refund_amount_kopecks, 0)

    def test_close_active_card_sums_refund_for_multiple_active_payments(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_active_card(session)
            session.add_all(
                [
                    Payment(
                        parking_card_id=card.id,
                        payment_date=date(2026, 5, 1),
                        period_from=date(2026, 5, 1),
                        period_to=date(2026, 5, 31),
                        amount_kopecks=310000,
                        status="active",
                    ),
                    Payment(
                        parking_card_id=card.id,
                        payment_date=date(2026, 6, 1),
                        period_from=date(2026, 6, 1),
                        period_to=date(2026, 6, 30),
                        amount_kopecks=300000,
                        status="active",
                    ),
                ]
            )
            session.flush()
            close_active_card(session, parking_card_id=card.id, closed_at=date(2026, 5, 21))
            session.commit()
            session.refresh(card)
            self.assertTrue(card.closed_with_active_paid_period)
            self.assertEqual(card.refund_days, 40)
            self.assertEqual(card.refund_amount_kopecks, 400000)

    def test_close_active_card_ignores_cancelled_payments(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_active_card(session)
            session.add(
                Payment(
                    parking_card_id=card.id,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=310000,
                    status="cancelled",
                )
            )
            session.flush()
            close_active_card(session, parking_card_id=card.id, closed_at=date(2026, 5, 21))
            session.commit()
            session.refresh(card)
            self.assertFalse(card.closed_with_active_paid_period)
            self.assertEqual(card.refund_days, 0)
            self.assertEqual(card.refund_amount_kopecks, 0)

    def test_close_active_card_ignores_past_active_payments(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_active_card(session)
            session.add(
                Payment(
                    parking_card_id=card.id,
                    payment_date=date(2026, 4, 1),
                    period_from=date(2026, 4, 1),
                    period_to=date(2026, 4, 30),
                    amount_kopecks=300000,
                    status="active",
                )
            )
            session.flush()
            close_active_card(session, parking_card_id=card.id, closed_at=date(2026, 5, 21))
            session.commit()
            session.refresh(card)
            self.assertFalse(card.closed_with_active_paid_period)
            self.assertEqual(card.refund_days, 0)
            self.assertEqual(card.refund_amount_kopecks, 0)

    def test_close_active_card_ignores_cancelled_future_payments(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_active_card(session)
            session.add(
                Payment(
                    parking_card_id=card.id,
                    payment_date=date(2026, 6, 1),
                    period_from=date(2026, 6, 1),
                    period_to=date(2026, 6, 30),
                    amount_kopecks=300000,
                    status="cancelled",
                )
            )
            session.flush()
            close_active_card(session, parking_card_id=card.id, closed_at=date(2026, 5, 21))
            session.commit()
            session.refresh(card)
            self.assertFalse(card.closed_with_active_paid_period)
            self.assertEqual(card.refund_days, 0)
            self.assertEqual(card.refund_amount_kopecks, 0)

    def test_close_active_card_partial_current_period_only(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_active_card(session)
            session.add(
                Payment(
                    parking_card_id=card.id,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=310000,
                    status="active",
                )
            )
            session.flush()
            close_active_card(session, parking_card_id=card.id, closed_at=date(2026, 5, 21))
            session.commit()
            session.refresh(card)
            self.assertEqual(card.refund_days, 10)
            self.assertEqual(card.refund_amount_kopecks, 100000)

    def test_close_missing_card(self) -> None:
        with self.SessionLocal() as session:
            with self.assertRaisesRegex(ValueError, "CARD_NOT_FOUND"):
                close_active_card(session, parking_card_id=999, closed_at=date(2026, 5, 21))

    def test_close_non_active_card(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_active_card(session)
            card.status = "closed"
            session.flush()
            with self.assertRaisesRegex(ValueError, "CARD_NOT_ACTIVE"):
                close_active_card(session, parking_card_id=card.id, closed_at=date(2026, 5, 21))

    def test_close_service_does_not_commit(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_active_card(session)
            card_id = card.id
            session.commit()
            close_active_card(session, parking_card_id=card_id, closed_at=date(2026, 5, 21))
            self.assertEqual(session.get(ParkingCard, card_id).status, "closed")
            session.rollback()
            self.assertEqual(session.get(ParkingCard, card_id).status, "active")


if __name__ == "__main__":
    unittest.main()
