import unittest

from parking_app.services.card_number_service import normalize_card_number, validate_card_number_required


class CardNumberServiceTests(unittest.TestCase):
    def test_normalize_trim(self) -> None:
        self.assertEqual(normalize_card_number(" 000001 "), "000001")

    def test_normalize_keep_zeros(self) -> None:
        self.assertEqual(normalize_card_number("000010"), "000010")

    def test_required(self) -> None:
        self.assertTrue(validate_card_number_required(" 1 "))
        self.assertFalse(validate_card_number_required("   "))


if __name__ == "__main__":
    unittest.main()
