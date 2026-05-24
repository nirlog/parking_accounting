from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from parking_app.ui.styles import build_accessible_stylesheet, resolve_theme_mode


class StylesTests(unittest.TestCase):
    def test_build_accessible_stylesheet_light_contains_light_table_colors(self) -> None:
        stylesheet = build_accessible_stylesheet("light")
        self.assertIn("#ffffff", stylesheet)
        self.assertIn("#111827", stylesheet)
        self.assertIn("selection-color", stylesheet)
        self.assertIn("QHeaderView::section", stylesheet)

    def test_build_accessible_stylesheet_dark_contains_dark_table_colors(self) -> None:
        stylesheet = build_accessible_stylesheet("dark")
        self.assertIn("#1f2937", stylesheet)
        self.assertIn("#f9fafb", stylesheet)
        self.assertIn("alternate-background-color", stylesheet)
        self.assertIn("selection-background-color", stylesheet)

    def test_resolve_theme_mode_accepts_known_modes(self) -> None:
        self.assertEqual(resolve_theme_mode("light"), "light")
        self.assertEqual(resolve_theme_mode("dark"), "dark")

    def test_resolve_theme_mode_uses_env_override(self) -> None:
        with patch.dict(os.environ, {"PARKING_APP_THEME": "dark"}, clear=False):
            self.assertEqual(resolve_theme_mode("system"), "dark")

    def test_invalid_theme_falls_back(self) -> None:
        result = resolve_theme_mode("invalid")
        self.assertIn(result, {"light", "dark"})


if __name__ == "__main__":
    unittest.main()
