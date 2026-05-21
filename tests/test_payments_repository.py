from __future__ import annotations

from importlib.util import find_spec
import unittest
from datetime import date

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from parking_app.database.db import Base
    from parking_app.database.models import Payment
    from parking_app.repositories.payments_repository import has_overlap_with_active_periods


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


if __name__ == "__main__":
    unittest.main()
