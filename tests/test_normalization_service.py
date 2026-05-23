import unittest

from parking_app.services.normalization_service import normalize_phone, normalize_state_number


class NormalizationServiceTests(unittest.TestCase):
    def test_phone_removes_non_digits(self) -> None:
        self.assertEqual(normalize_phone("+7 921 443-15-83"), "79214431583")

    def test_phone_replaces_8_prefix(self) -> None:
        self.assertEqual(normalize_phone("8 (921) 443-15-83"), "79214431583")

    def test_phone_adds_7_for_ten_digits(self) -> None:
        self.assertEqual(normalize_phone("9214431583"), "79214431583")

    def test_state_number_latin_to_cyrillic(self) -> None:
        self.assertEqual(normalize_state_number("A767AB178"), "А767АВ178")

    def test_state_number_strips_spaces_and_hyphens(self) -> None:
        self.assertEqual(normalize_state_number("а-767-ав 178"), "А767АВ178")


if __name__ == "__main__":
    unittest.main()
