from datetime import date
import unittest

from parking_app.app.constants import PaymentStatus
from parking_app.services.payment_service import (
    calculate_paid_until,
    calculate_payment_status,
    periods_overlap,
)


class PaymentServiceTests(unittest.TestCase):
    def test_calculate_paid_until_empty(self) -> None:
        self.assertIsNone(calculate_paid_until([]))

    def test_calculate_paid_until_max(self) -> None:
        d1 = date(2026, 9, 27)
        d2 = date(2026, 10, 27)
        self.assertEqual(calculate_paid_until([d1, d2]), d2)

    def test_status_no_payments(self) -> None:
        status = calculate_payment_status(None, today=date(2026, 5, 21), warning_days=3)
        self.assertEqual(status, PaymentStatus.NO_PAYMENTS)

    def test_status_overdue(self) -> None:
        status = calculate_payment_status(date(2026, 5, 20), today=date(2026, 5, 21), warning_days=3)
        self.assertEqual(status, PaymentStatus.OVERDUE)

    def test_status_expiring_today(self) -> None:
        status = calculate_payment_status(date(2026, 5, 21), today=date(2026, 5, 21), warning_days=3)
        self.assertEqual(status, PaymentStatus.EXPIRING_SOON)

    def test_status_expiring_on_border(self) -> None:
        status = calculate_payment_status(date(2026, 5, 24), today=date(2026, 5, 21), warning_days=3)
        self.assertEqual(status, PaymentStatus.EXPIRING_SOON)

    def test_status_paid_after_border(self) -> None:
        status = calculate_payment_status(date(2026, 5, 25), today=date(2026, 5, 21), warning_days=3)
        self.assertEqual(status, PaymentStatus.PAID)

    def test_overlap_true_on_boundary(self) -> None:
        self.assertTrue(
            periods_overlap(
                new_period_from=date(2026, 1, 31),
                new_period_to=date(2026, 2, 15),
                existing_period_from=date(2026, 1, 1),
                existing_period_to=date(2026, 1, 31),
            )
        )

    def test_overlap_false_for_next_day(self) -> None:
        self.assertFalse(
            periods_overlap(
                new_period_from=date(2026, 2, 1),
                new_period_to=date(2026, 2, 28),
                existing_period_from=date(2026, 1, 1),
                existing_period_to=date(2026, 1, 31),
            )
        )


if __name__ == "__main__":
    unittest.main()
