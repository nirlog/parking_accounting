from datetime import date
import unittest

from parking_app.services.payments_view_service import calculate_payments_summary, filter_payments_by_period


class PaymentsViewServiceTests(unittest.TestCase):
    def test_calculate_summary(self) -> None:
        summary = calculate_payments_summary(
            [
                {"status": "active", "amount_kopecks": 800000},
                {"status": "active", "amount_kopecks": 900000},
                {"status": "cancelled", "amount_kopecks": 700000},
            ]
        )
        self.assertEqual(summary.active_count, 2)
        self.assertEqual(summary.cancelled_count, 1)
        self.assertEqual(summary.active_amount_kopecks, 1700000)

    def test_filter_by_period(self) -> None:
        rows = [
            {"payment_date": date(2026, 5, 1), "status": "active"},
            {"payment_date": date(2026, 5, 20), "status": "active"},
            {"payment_date": date(2026, 6, 1), "status": "cancelled"},
        ]
        filtered = filter_payments_by_period(rows, date_from=date(2026, 5, 1), date_to=date(2026, 5, 31))
        self.assertEqual(len(filtered), 2)


if __name__ == "__main__":
    unittest.main()
