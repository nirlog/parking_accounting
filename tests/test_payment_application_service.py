from datetime import date
import unittest

from parking_app.services.payment_application_service import (
    PAYMENT_AMOUNT_INVALID,
    PAYMENT_DATE_REQUIRED,
    PAYMENT_PERIOD_OVERLAP,
    PERIOD_FROM_REQUIRED,
    PERIOD_ORDER_INVALID,
    PERIOD_TO_REQUIRED,
    PaymentDraft,
    validate_payment_draft_fields,
    validate_payment_overlap_in_memory,
)


class PaymentApplicationServiceTests(unittest.TestCase):
    def test_required_date(self) -> None:
        result = validate_payment_draft_fields(
            PaymentDraft(parking_card_id=1, payment_date=None, period_from=date.today(), period_to=date.today(), amount_kopecks=1)
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, PAYMENT_DATE_REQUIRED)

    def test_required_period_from(self) -> None:
        result = validate_payment_draft_fields(
            PaymentDraft(parking_card_id=1, payment_date=date.today(), period_from=None, period_to=date.today(), amount_kopecks=1)
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, PERIOD_FROM_REQUIRED)

    def test_required_period_to(self) -> None:
        result = validate_payment_draft_fields(
            PaymentDraft(parking_card_id=1, payment_date=date.today(), period_from=date.today(), period_to=None, amount_kopecks=1)
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, PERIOD_TO_REQUIRED)

    def test_period_order(self) -> None:
        result = validate_payment_draft_fields(
            PaymentDraft(
                parking_card_id=1,
                payment_date=date(2026, 5, 21),
                period_from=date(2026, 5, 22),
                period_to=date(2026, 5, 21),
                amount_kopecks=1,
            )
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, PERIOD_ORDER_INVALID)

    def test_amount(self) -> None:
        result = validate_payment_draft_fields(
            PaymentDraft(
                parking_card_id=1,
                payment_date=date(2026, 5, 21),
                period_from=date(2026, 5, 21),
                period_to=date(2026, 5, 21),
                amount_kopecks=0,
            )
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, PAYMENT_AMOUNT_INVALID)

    def test_overlap_in_memory(self) -> None:
        result = validate_payment_overlap_in_memory(
            new_period_from=date(2026, 1, 31),
            new_period_to=date(2026, 2, 15),
            existing_active_periods=[(date(2026, 1, 1), date(2026, 1, 31))],
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, PAYMENT_PERIOD_OVERLAP)

    def test_no_overlap_in_memory(self) -> None:
        result = validate_payment_overlap_in_memory(
            new_period_from=date(2026, 2, 1),
            new_period_to=date(2026, 2, 28),
            existing_active_periods=[(date(2026, 1, 1), date(2026, 1, 31))],
        )
        self.assertTrue(result.ok)
        self.assertIsNone(result.error)


if __name__ == "__main__":
    unittest.main()
