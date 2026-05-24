from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from parking_app.services.settings_service import (
    get_ui_theme_mode,
    get_warning_days,
    parse_warning_days,
    set_ui_theme_mode,
)


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

    @patch("parking_app.services.settings_service.get_setting")
    def test_get_ui_theme_mode_default_system(self, mock_get_setting: Mock) -> None:
        mock_get_setting.return_value = None
        self.assertEqual(get_ui_theme_mode(session=object()), "system")

    @patch("parking_app.services.settings_service.set_setting")
    def test_set_ui_theme_mode_saves_light(self, mock_set_setting: Mock) -> None:
        session = object()
        set_ui_theme_mode(session=session, mode="light")
        mock_set_setting.assert_called_once_with(session, "ui.theme", "light")

    def test_set_ui_theme_mode_invalid(self) -> None:
        with self.assertRaisesRegex(ValueError, "INVALID_THEME_MODE"):
            set_ui_theme_mode(session=object(), mode="invalid")


if __name__ == "__main__":
    unittest.main()
