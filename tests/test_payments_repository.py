from __future__ import annotations

from importlib.util import find_spec
import unittest
from datetime import UTC, date, datetime

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from parking_app.database.db import Base
    from parking_app.database.models import Payment
    from parking_app.repositories.payments_repository import cancel_payment, create_payment, has_overlap_with_active_periods


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class PaymentsRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def test_detects_overlap_with_active_payment(self) -> None:
        with self.SessionLocal() as session:
            session.add(
                Payment(
                    parking_card_id=1,
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
                    parking_card_id=1,
                    period_from=date(2026, 5, 31),
                    period_to=date(2026, 6, 15),
                )
            )

    def test_ignores_cancelled_payment(self) -> None:
        with self.SessionLocal() as session:
            session.add(
                Payment(
                    parking_card_id=1,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=800000,
                    status="cancelled",
                )
            )
            session.commit()

            self.assertFalse(
                has_overlap_with_active_periods(
                    session,
                    parking_card_id=1,
                    period_from=date(2026, 5, 15),
                    period_to=date(2026, 5, 20),
                )
            )

    def test_no_overlap_adjacent_period(self) -> None:
        with self.SessionLocal() as session:
            session.add(
                Payment(
                    parking_card_id=1,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=800000,
                    status="active",
                )
            )
            session.commit()

            self.assertFalse(
                has_overlap_with_active_periods(
                    session,
                    parking_card_id=1,
                    period_from=date(2026, 6, 1),
                    period_to=date(2026, 6, 30),
                )
            )

    def test_cancel_metadata_fields_are_persisted(self) -> None:
        with self.SessionLocal() as session:
            cancelled_at = datetime(2026, 5, 21, 10, 0, tzinfo=UTC)
            payment = Payment(
                parking_card_id=1,
                payment_date=date(2026, 5, 1),
                period_from=date(2026, 5, 1),
                period_to=date(2026, 5, 31),
                amount_kopecks=800000,
                status="cancelled",
                cancel_reason="Ошибка кассира",
                cancelled_at=cancelled_at,
            )
            session.add(payment)
            session.commit()
            session.refresh(payment)

            self.assertEqual(payment.cancel_reason, "Ошибка кассира")
            self.assertIsNotNone(payment.cancelled_at)

    def test_create_payment_and_cancel_payment(self) -> None:
        with self.SessionLocal() as session:
            payment = create_payment(
                session,
                parking_card_id=1,
                payment_date=date(2026, 5, 1),
                period_from=date(2026, 5, 1),
                period_to=date(2026, 5, 31),
                amount_kopecks=800000,
                receipt_number="483",
                fiscal_number="ФД85",
                accepted_by="Колобков",
            )
            session.commit()
            self.assertEqual(payment.status, "active")
            self.assertEqual(payment.receipt_number, "483")

            cancelled_at = datetime(2026, 5, 21, 10, 0, tzinfo=UTC)
            updated = cancel_payment(
                session,
                payment_id=payment.id,
                cancel_reason="Ошибка кассира",
                cancelled_at=cancelled_at,
            )
            session.commit()

            self.assertIsNotNone(updated)
            assert updated is not None
            self.assertEqual(updated.status, "cancelled")
            self.assertEqual(updated.cancel_reason, "Ошибка кассира")

    def test_create_payment_rejects_overlap(self) -> None:
        with self.SessionLocal() as session:
            create_payment(
                session,
                parking_card_id=1,
                payment_date=date(2026, 5, 1),
                period_from=date(2026, 5, 1),
                period_to=date(2026, 5, 31),
                amount_kopecks=800000,
            )
            session.commit()

            with self.assertRaises(ValueError):
                create_payment(
                    session,
                    parking_card_id=1,
                    payment_date=date(2026, 5, 2),
                    period_from=date(2026, 5, 15),
                    period_to=date(2026, 6, 1),
                    amount_kopecks=500000,
                )

    def test_cancel_payment_does_not_overwrite_existing_cancellation(self) -> None:
        with self.SessionLocal() as session:
            first_time = datetime(2026, 5, 21, 10, 0, tzinfo=UTC)
            second_time = datetime(2026, 5, 21, 11, 0, tzinfo=UTC)
            payment = create_payment(
                session,
                parking_card_id=1,
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
            self.assertIsNotNone(payment.cancelled_at)
            assert payment.cancelled_at is not None
            self.assertEqual(payment.cancelled_at.replace(tzinfo=UTC), first_time)


if __name__ == "__main__":
    unittest.main()
