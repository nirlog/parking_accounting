import unittest

from parking_app.services.receipt_service import normalize_fiscal_number, normalize_receipt_number


class ReceiptServiceTests(unittest.TestCase):
    def test_normalize_receipt_number(self) -> None:
        self.assertEqual(normalize_receipt_number(" 483 "), "483")
        self.assertIsNone(normalize_receipt_number("   "))
        self.assertIsNone(normalize_receipt_number(None))

    def test_normalize_fiscal_number(self) -> None:
        self.assertEqual(normalize_fiscal_number(" фд 85 "), "ФД 85")
        self.assertIsNone(normalize_fiscal_number("  "))
        self.assertIsNone(normalize_fiscal_number(None))


if __name__ == "__main__":
    unittest.main()
