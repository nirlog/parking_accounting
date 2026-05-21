import unittest

from parking_app.services.phone_service import format_phone_ru


class PhoneServiceTests(unittest.TestCase):
    def test_format_canonical_ru_phone(self) -> None:
        self.assertEqual(format_phone_ru("79214431583"), "+7 921 443-15-83")

    def test_format_empty(self) -> None:
        self.assertEqual(format_phone_ru(None), "")
        self.assertEqual(format_phone_ru(""), "")

    def test_format_fallback_for_unexpected_shape(self) -> None:
        self.assertEqual(format_phone_ru("12345"), "12345")


if __name__ == "__main__":
    unittest.main()
