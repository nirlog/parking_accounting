from datetime import date
import unittest

from parking_app.services.card_closing_service import calculate_close_card_result


class CardClosingServiceTests(unittest.TestCase):
    def test_no_active_payment(self) -> None:
        result = calculate_close_card_result(
            closed_at=date(2026, 9, 20),
            paid_period_from=None,
            paid_period_to=None,
            paid_amount_kopecks=None,
        )
        self.assertFalse(result.closed_with_active_paid_period)
        self.assertEqual(result.refund_days, 0)
        self.assertEqual(result.refund_amount_kopecks, 0)

    def test_with_refund(self) -> None:
        result = calculate_close_card_result(
            closed_at=date(2026, 9, 20),
            paid_period_from=date(2026, 9, 1),
            paid_period_to=date(2026, 9, 30),
            paid_amount_kopecks=900000,
        )
        self.assertTrue(result.closed_with_active_paid_period)
        self.assertEqual(result.refund_days, 10)
        self.assertEqual(result.refund_amount_kopecks, 300000)

    def test_no_refund_when_period_is_over(self) -> None:
        result = calculate_close_card_result(
            closed_at=date(2026, 9, 30),
            paid_period_from=date(2026, 9, 1),
            paid_period_to=date(2026, 9, 30),
            paid_amount_kopecks=900000,
        )
        self.assertFalse(result.closed_with_active_paid_period)
        self.assertEqual(result.refund_days, 0)
        self.assertEqual(result.refund_amount_kopecks, 0)


if __name__ == "__main__":
    unittest.main()
