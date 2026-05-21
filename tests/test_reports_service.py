from datetime import date
import unittest

from parking_app.services.reports_service import (
    build_places_occupancy_summary,
    build_refund_report_items,
    build_overdue_items,
    build_payments_period_summary,
    calculate_overdue_days,
)


class ReportsServiceTests(unittest.TestCase):
    def test_calculate_overdue_days(self) -> None:
        self.assertEqual(calculate_overdue_days(paid_until=date(2026, 5, 20), today=date(2026, 5, 21)), 1)
        self.assertEqual(calculate_overdue_days(paid_until=date(2026, 5, 21), today=date(2026, 5, 21)), 0)

    def test_build_overdue_items(self) -> None:
        items = build_overdue_items(
            [
                {"card_id": 1, "paid_until": date(2026, 5, 20), "payment_status": "Просрочено"},
                {"card_id": 2, "paid_until": date(2026, 5, 22), "payment_status": "Оплачено"},
                {"card_id": 3, "paid_until": None, "payment_status": "Нет оплат"},
            ],
            today=date(2026, 5, 21),
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].card_id, 1)
        self.assertEqual(items[0].overdue_days, 1)

    def test_build_payments_period_summary(self) -> None:
        summary = build_payments_period_summary(
            [
                {"status": "active", "amount_kopecks": 800000},
                {"status": "active", "amount_kopecks": 500000},
                {"status": "cancelled", "amount_kopecks": 999999},
                {"status": "active", "amount_kopecks": None},
            ]
        )
        self.assertEqual(summary.active_count, 3)
        self.assertEqual(summary.cancelled_count, 1)
        self.assertEqual(summary.active_amount_kopecks, 1300000)

    def test_build_places_occupancy_summary(self) -> None:
        summary = build_places_occupancy_summary(
            [
                {"display_status": "occupied"},
                {"display_status": "occupied"},
                {"display_status": "free"},
                {"display_status": "repair"},
                {"display_status": "reserved"},
            ]
        )
        self.assertEqual(summary.occupied_count, 2)
        self.assertEqual(summary.free_count, 1)

    def test_build_refund_report_items(self) -> None:
        items = build_refund_report_items(
            [
                {
                    "card_number": "000001",
                    "fio": "Иванов Иван",
                    "state_number": "А123АА178",
                    "place_number": "101",
                    "closed_at": date(2026, 5, 21),
                    "paid_until": date(2026, 5, 31),
                    "refund_days": 10,
                    "refund_amount_kopecks": 300000,
                    "refund_note": "По заявлению",
                },
                {
                    "card_number": "000002",
                    "fio": "Петров Пётр",
                    "closed_at": date(2026, 5, 21),
                    "refund_amount_kopecks": 0,
                },
            ]
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].card_number, "000001")
        self.assertEqual(items[0].refund_days, 10)


if __name__ == "__main__":
    unittest.main()
