from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from parking_app.services.settings_service import (
    ParkingInfo,
    get_parking_info,
    get_ui_theme_mode,
    get_warning_days,
    parse_warning_days,
    set_parking_info,
    set_ui_theme_mode,
    set_warning_days,
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

    @patch("parking_app.services.settings_service.set_setting")
    def test_set_warning_days_valid(self, mock_set_setting: Mock) -> None:
        session = object()
        set_warning_days(session=session, days=5)
        mock_set_setting.assert_called_once_with(session, "payment_warning_days", "5")

    def test_set_warning_days_invalid(self) -> None:
        with self.assertRaisesRegex(ValueError, "INVALID_WARNING_DAYS"):
            set_warning_days(session=object(), days=-1)
        with self.assertRaisesRegex(ValueError, "INVALID_WARNING_DAYS"):
            set_warning_days(session=object(), days=61)

    @patch("parking_app.services.settings_service.get_setting")
    def test_get_warning_days_default(self, mock_get_setting: Mock) -> None:
        mock_get_setting.return_value = None
        self.assertEqual(get_warning_days(session=object()), 3)

    @patch("parking_app.services.settings_service.get_setting")
    def test_get_parking_info_default(self, mock_get_setting: Mock) -> None:
        mock_get_setting.return_value = None
        info = get_parking_info(session=object())
        self.assertEqual(info, ParkingInfo())

    @patch("parking_app.services.settings_service.get_setting")
    @patch("parking_app.services.settings_service.set_setting")
    def test_set_and_get_parking_info(self, mock_set_setting: Mock, mock_get_setting: Mock) -> None:
        session = object()
        expected = ParkingInfo(name="Стоянка №1", address="СПб", phone="+7...", note="Реквизиты")
        set_parking_info(session, expected)
        self.assertEqual(mock_set_setting.call_count, 4)
        mock_get_setting.side_effect = [expected.name, expected.address, expected.phone, expected.note]
        actual = get_parking_info(session)
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
