from datetime import date
import unittest

from parking_app.services.payment_service import calculate_refund


class RefundCalculationTests(unittest.TestCase):
    def test_example_from_spec(self) -> None:
        days, amount = calculate_refund(
            period_from=date(2026, 9, 1),
            period_to=date(2026, 9, 30),
            amount_kopecks=900000,
            closed_at=date(2026, 9, 20),
        )
        self.assertEqual(days, 10)
        self.assertEqual(amount, 300000)

    def test_no_refund_if_closed_on_or_after_period_end(self) -> None:
        days, amount = calculate_refund(
            period_from=date(2026, 9, 1),
            period_to=date(2026, 9, 30),
            amount_kopecks=900000,
            closed_at=date(2026, 9, 30),
        )
        self.assertEqual((days, amount), (0, 0))

    def test_full_refund_if_closed_before_period_start(self) -> None:
        days, amount = calculate_refund(
            period_from=date(2026, 9, 1),
            period_to=date(2026, 9, 30),
            amount_kopecks=900000,
            closed_at=date(2026, 8, 31),
        )
        self.assertEqual(days, 30)
        self.assertEqual(amount, 900000)


if __name__ == "__main__":
    unittest.main()
