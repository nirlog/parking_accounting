from datetime import datetime
import unittest

from parking_app.services.payment_cancel_service import (
    build_cancel_payment_result,
    validate_cancel_reason,
)


class PaymentCancelServiceTests(unittest.TestCase):
    def test_validate_cancel_reason(self) -> None:
        self.assertTrue(validate_cancel_reason("Ошибка кассира"))
        self.assertFalse(validate_cancel_reason("   "))

    def test_build_cancel_payment_result(self) -> None:
        now = datetime(2026, 5, 21, 10, 15, 0)
        result = build_cancel_payment_result(reason=" Ошибка кассира ", now=now)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(result.cancel_reason, "Ошибка кассира")
        self.assertEqual(result.cancelled_at, now)

    def test_build_cancel_payment_requires_reason(self) -> None:
        with self.assertRaises(ValueError):
            build_cancel_payment_result(reason="  ")


if __name__ == "__main__":
    unittest.main()
