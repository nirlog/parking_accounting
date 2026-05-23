import unittest
from unittest.mock import Mock, patch

from parking_app.services.settings_service import get_warning_days, parse_warning_days


class SettingsServiceTests(unittest.TestCase):
    def test_parse_warning_days_default_for_none(self) -> None:
        self.assertEqual(parse_warning_days(None), 3)

    def test_parse_warning_days_default_for_invalid(self) -> None:
        self.assertEqual(parse_warning_days("abc"), 3)

    def test_parse_warning_days_default_for_negative(self) -> None:
        self.assertEqual(parse_warning_days("-1"), 3)

    def test_parse_warning_days_value(self) -> None:
        self.assertEqual(parse_warning_days("7"), 7)

    @patch("parking_app.services.settings_service.get_setting_value")
    def test_get_warning_days(self, mock_get_setting_value: Mock) -> None:
        mock_get_setting_value.return_value = "5"
        self.assertEqual(get_warning_days(session=object()), 5)
        mock_get_setting_value.assert_called_once()


if __name__ == "__main__":
    unittest.main()
