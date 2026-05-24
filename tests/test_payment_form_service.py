from __future__ import annotations

from datetime import date
from importlib.util import find_spec
import unittest

from parking_app.services.payment_form_service import get_next_payment_period, parse_amount_to_kopecks

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from parking_app.database.db import Base
    from parking_app.database.models import Payment


class PaymentFormServiceAmountTests(unittest.TestCase):
    def test_parse_amount_to_kopecks(self) -> None:
        self.assertEqual(parse_amount_to_kopecks("8000"), 800000)
        self.assertEqual(parse_amount_to_kopecks("8000.50"), 800050)
        self.assertEqual(parse_amount_to_kopecks("8000,50"), 800050)

    def test_parse_amount_invalid(self) -> None:
        with self.assertRaisesRegex(ValueError, "AMOUNT_REQUIRED"):
            parse_amount_to_kopecks("")
        with self.assertRaisesRegex(ValueError, "AMOUNT_MUST_BE_POSITIVE"):
            parse_amount_to_kopecks("-1")
        with self.assertRaisesRegex(ValueError, "AMOUNT_MUST_BE_POSITIVE"):
            parse_amount_to_kopecks("0")


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class PaymentFormServicePeriodTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def test_get_next_payment_period_without_payments(self) -> None:
        with self.SessionLocal() as session:
            period_from, period_to = get_next_payment_period(session, parking_card_id=1, card_start_date=date(2026, 1, 28))
            self.assertEqual(period_from, date(2026, 1, 28))
            self.assertEqual(period_to, date(2026, 2, 27))

    def test_get_next_payment_period_after_active_payment(self) -> None:
        with self.SessionLocal() as session:
            session.add(
                Payment(
                    parking_card_id=1,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=100,
                    status="active",
                )
            )
            session.commit()
            period_from, period_to = get_next_payment_period(session, parking_card_id=1, card_start_date=date(2026, 1, 1))
            self.assertEqual(period_from, date(2026, 6, 1))
            self.assertEqual(period_to, date(2026, 6, 30))

    def test_cancelled_payments_do_not_affect_next_period(self) -> None:
        with self.SessionLocal() as session:
            session.add(
                Payment(
                    parking_card_id=1,
                    payment_date=date(2026, 6, 1),
                    period_from=date(2026, 6, 1),
                    period_to=date(2026, 6, 30),
                    amount_kopecks=100,
                    status="cancelled",
                )
            )
            session.commit()
            period_from, period_to = get_next_payment_period(session, parking_card_id=1, card_start_date=date(2026, 2, 1))
            self.assertEqual(period_from, date(2026, 2, 1))
            self.assertEqual(period_to, date(2026, 2, 28))


if __name__ == "__main__":
    unittest.main()
