from __future__ import annotations

from importlib.util import find_spec
import unittest
from datetime import UTC, date, datetime

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from parking_app.database.db import Base
    from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle
    from parking_app.repositories.payments_repository import cancel_payment, create_payment, has_overlap_with_active_periods


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class PaymentsRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def _create_card(self, session, *, status: str = "active", place_number: str = "101", state_number: str = "А123АА178") -> ParkingCard:
        client = Client(surname="Иванов", name="Иван")
        session.add(client)
        session.flush()
        vehicle = Vehicle(client_id=client.id, state_number=state_number)
        session.add(vehicle)
        place = ParkingPlace(place_number=place_number, status="free")
        session.add(place)
        session.flush()
        card = ParkingCard(
            card_number=f"C-{place_number}-{state_number}",
            client_id=client.id,
            vehicle_id=vehicle.id,
            place_id=place.id,
            start_date=date(2026, 1, 1),
            status=status,
        )
        session.add(card)
        session.flush()
        return card

    def test_create_payment_success_for_active_card(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session, status="active")
            payment = create_payment(
                session,
                parking_card_id=card.id,
                payment_date=date(2026, 5, 1),
                period_from=date(2026, 5, 1),
                period_to=date(2026, 5, 31),
                amount_kopecks=800000,
            )
            session.commit()
            self.assertEqual(payment.status, "active")

    def test_create_payment_rejects_closed_card(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session, status="closed")
            with self.assertRaisesRegex(ValueError, "PAYMENT_CARD_NOT_ACTIVE"):
                create_payment(
                    session,
                    parking_card_id=card.id,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=800000,
                )

    def test_create_payment_rejects_archived_card(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session, status="archived")
            with self.assertRaisesRegex(ValueError, "PAYMENT_CARD_NOT_ACTIVE"):
                create_payment(
                    session,
                    parking_card_id=card.id,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=800000,
                )

    def test_create_payment_rejects_missing_card(self) -> None:
        with self.SessionLocal() as session:
            with self.assertRaisesRegex(ValueError, "PAYMENT_CARD_NOT_FOUND"):
                create_payment(
                    session,
                    parking_card_id=999,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=800000,
                )

    def test_detects_overlap_with_active_payment(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session)
            session.add(
                Payment(
                    parking_card_id=card.id,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=800000,
                    status="active",
                )
            )
            session.commit()
            self.assertTrue(
                has_overlap_with_active_periods(
                    session,
                    parking_card_id=card.id,
                    period_from=date(2026, 5, 31),
                    period_to=date(2026, 6, 15),
                )
            )

    def test_create_payment_rejects_overlap(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session)
            create_payment(
                session,
                parking_card_id=card.id,
                payment_date=date(2026, 5, 1),
                period_from=date(2026, 5, 1),
                period_to=date(2026, 5, 31),
                amount_kopecks=800000,
            )
            session.commit()
            with self.assertRaisesRegex(ValueError, "PAYMENT_PERIOD_OVERLAP"):
                create_payment(
                    session,
                    parking_card_id=card.id,
                    payment_date=date(2026, 5, 2),
                    period_from=date(2026, 5, 15),
                    period_to=date(2026, 6, 1),
                    amount_kopecks=500000,
                )

    def test_cancel_payment_does_not_overwrite_existing_cancellation(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session)
            first_time = datetime(2026, 5, 21, 10, 0, tzinfo=UTC)
            second_time = datetime(2026, 5, 21, 11, 0, tzinfo=UTC)
            payment = create_payment(
                session,
                parking_card_id=card.id,
                payment_date=date(2026, 5, 1),
                period_from=date(2026, 5, 1),
                period_to=date(2026, 5, 31),
                amount_kopecks=800000,
            )
            cancel_payment(session, payment_id=payment.id, cancel_reason="Первичная ошибка", cancelled_at=first_time)
            session.commit()

            cancel_payment(session, payment_id=payment.id, cancel_reason="Повторная причина", cancelled_at=second_time)
            session.commit()
            session.refresh(payment)
            self.assertEqual(payment.cancel_reason, "Первичная ошибка")


if __name__ == "__main__":
    unittest.main()
