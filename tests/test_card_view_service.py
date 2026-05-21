from datetime import date
import unittest

from parking_app.app.constants import PaymentStatus
from parking_app.services.card_view_service import build_card_payment_view


class CardViewServiceTests(unittest.TestCase):
    def test_no_payments(self) -> None:
        view = build_card_payment_view(active_period_ends=[], today=date(2026, 5, 21), warning_days=3)
        self.assertIsNone(view.paid_until)
        self.assertEqual(view.payment_status, PaymentStatus.NO_PAYMENTS)

    def test_uses_latest_paid_until(self) -> None:
        view = build_card_payment_view(
            active_period_ends=[date(2026, 5, 22), date(2026, 5, 30)],
            today=date(2026, 5, 21),
            warning_days=3,
        )
        self.assertEqual(view.paid_until, date(2026, 5, 30))
        self.assertEqual(view.payment_status, PaymentStatus.PAID)

    def test_expiring_soon(self) -> None:
        view = build_card_payment_view(
            active_period_ends=[date(2026, 5, 24)],
            today=date(2026, 5, 21),
            warning_days=3,
        )
        self.assertEqual(view.payment_status, PaymentStatus.EXPIRING_SOON)


if __name__ == "__main__":
    unittest.main()
