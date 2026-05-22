from datetime import date
import unittest

from parking_app.services.payment_period_suggestion_service import suggest_next_payment_period


class PaymentPeriodSuggestionServiceTests(unittest.TestCase):
    def test_first_payment_from_start_date(self) -> None:
        p = suggest_next_payment_period(start_date=date(2026, 8, 28), latest_paid_until=None)
        self.assertEqual(p.period_from, date(2026, 8, 28))
        self.assertEqual(p.period_to, date(2026, 9, 27))

    def test_next_payment_from_latest_paid_until_plus_one(self) -> None:
        p = suggest_next_payment_period(start_date=date(2026, 8, 28), latest_paid_until=date(2026, 9, 27))
        self.assertEqual(p.period_from, date(2026, 9, 28))
        self.assertEqual(p.period_to, date(2026, 10, 27))


if __name__ == "__main__":
    unittest.main()
