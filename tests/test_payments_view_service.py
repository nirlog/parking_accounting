from datetime import date
import unittest

from parking_app.services.payments_view_service import calculate_payments_summary, filter_payments, filter_payments_by_period


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

    def test_filter_payments_by_composite_filters(self) -> None:
        rows = [
            {
                "fio": "Иванов Иван",
                "state_number": "А123АА178",
                "place_number": "101",
                "accepted_by": "Колобков",
                "status": "active",
                "receipt_number": "483",
            },
            {
                "fio": "Петров Пётр",
                "state_number": "В555ВВ178",
                "place_number": "102",
                "accepted_by": "Сидоров",
                "status": "cancelled",
                "receipt_number": "777",
            },
        ]
        filtered = filter_payments(
            rows,
            query="иванов",
            place_number="101",
            state_number="А123",
            accepted_by="колоб",
            status="active",
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["place_number"], "101")


if __name__ == "__main__":
    unittest.main()
