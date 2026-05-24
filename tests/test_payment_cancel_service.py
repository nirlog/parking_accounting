from __future__ import annotations

from datetime import UTC, date, datetime
from importlib.util import find_spec
import unittest

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from parking_app.database.db import Base
    from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle
    from parking_app.services.payment_cancel_service import cancel_active_payment


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class PaymentCancelServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def _create_active_payment(self, session) -> Payment:
        client = Client(surname="Иванов", name="Иван")
        session.add(client)
        session.flush()
        vehicle = Vehicle(client_id=client.id, state_number="А123АА178")
        place = ParkingPlace(place_number="101", status="free")
        session.add_all([vehicle, place])
        session.flush()
        card = ParkingCard(
            card_number="000001",
            client_id=client.id,
            vehicle_id=vehicle.id,
            place_id=place.id,
            start_date=date(2026, 5, 1),
            status="active",
            vehicle_state_number="А123АА178",
        )
        session.add(card)
        session.flush()
        payment = Payment(
            parking_card_id=card.id,
            payment_date=date(2026, 5, 1),
            period_from=date(2026, 5, 1),
            period_to=date(2026, 5, 31),
            amount_kopecks=800000,
            status="active",
        )
        session.add(payment)
        session.flush()
        return payment

    def test_successful_cancel(self) -> None:
        with self.SessionLocal() as session:
            payment = self._create_active_payment(session)
            payment_id = payment.id
            at = datetime(2026, 5, 21, 10, 0, tzinfo=UTC)
            cancelled = cancel_active_payment(
                session,
                payment_id=payment_id,
                cancel_reason="Ошибка кассира",
                cancelled_at=at,
            )
            self.assertEqual(cancelled.status, "cancelled")
            self.assertEqual(cancelled.cancel_reason, "Ошибка кассира")
            self.assertEqual(cancelled.cancelled_at, at)

    def test_missing_payment(self) -> None:
        with self.SessionLocal() as session:
            with self.assertRaisesRegex(ValueError, "PAYMENT_NOT_FOUND"):
                cancel_active_payment(
                    session,
                    payment_id=999,
                    cancel_reason="x",
                    cancelled_at=datetime.now(UTC),
                )

    def test_cancelled_payment_rejected(self) -> None:
        with self.SessionLocal() as session:
            payment = self._create_active_payment(session)
            payment_id = payment.id
            payment.status = "cancelled"
            with self.assertRaisesRegex(ValueError, "PAYMENT_NOT_ACTIVE"):
                cancel_active_payment(
                    session,
                    payment_id=payment_id,
                    cancel_reason="x",
                    cancelled_at=datetime.now(UTC),
                )

    def test_empty_reason_required(self) -> None:
        with self.SessionLocal() as session:
            payment = self._create_active_payment(session)
            payment_id = payment.id
            with self.assertRaisesRegex(ValueError, "PAYMENT_CANCEL_REASON_REQUIRED"):
                cancel_active_payment(
                    session,
                    payment_id=payment_id,
                    cancel_reason="   ",
                    cancelled_at=datetime.now(UTC),
                )

    def test_service_does_not_commit(self) -> None:
        with self.SessionLocal() as session:
            payment = self._create_active_payment(session)
            session.commit()
            payment_id = payment.id
            cancel_active_payment(
                session,
                payment_id=payment_id,
                cancel_reason="Ошибка",
                cancelled_at=datetime.now(UTC),
            )
            session.rollback()
            refreshed = session.get(Payment, payment_id)
            assert refreshed is not None
            self.assertEqual(refreshed.status, "active")


if __name__ == "__main__":
    unittest.main()
