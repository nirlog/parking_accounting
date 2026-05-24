from __future__ import annotations

import importlib
from importlib.util import find_spec
import os
import subprocess
import sys
import unittest
from unittest.mock import Mock

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

PYSIDE6_AVAILABLE = False
try:
    importlib.import_module("PySide6.QtWidgets")
    PYSIDE6_AVAILABLE = True
except Exception:
    PYSIDE6_AVAILABLE = False

if SQLALCHEMY_AVAILABLE:
    from parking_app.main import bootstrap


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class MainBootstrapTests(unittest.TestCase):
    def test_bootstrap_returns_paths(self) -> None:
        info = bootstrap()
        self.assertIn("db_path", info)
        self.assertIn("exports_dir", info)
        self.assertIn("backups_dir", info)

    def test_main_script_runs_bootstrap_only(self) -> None:
        proc = subprocess.run(
            [sys.executable, "parking_app/main.py", "--bootstrap-only"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("DB:", proc.stdout)
        self.assertIn("Exports:", proc.stdout)
        self.assertIn("Backups:", proc.stdout)


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 is not installed or unavailable")
class MainWindowSmokeTests(unittest.TestCase):
    def test_main_window_structure(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        qt_widgets = importlib.import_module("PySide6.QtWidgets")
        QApplication = qt_widgets.QApplication
        QTabWidget = qt_widgets.QTabWidget

        from parking_app.ui.main_window import MainWindow
        from parking_app.ui.styles import apply_large_accessible_style

        app = QApplication.instance() or QApplication([])

        window = MainWindow()

        self.assertEqual(window.windowTitle(), "Автостоянка — учёт")
        self.assertGreaterEqual(window.minimumWidth(), 1200)
        self.assertGreaterEqual(window.minimumHeight(), 720)

        central = window.centralWidget()
        self.assertIsNotNone(central)
        self.assertIsInstance(central, QTabWidget)
        assert isinstance(central, QTabWidget)

        self.assertEqual(central.count(), 5)
        expected_titles = ["Карточки", "Оплаты", "Места", "Отчёты", "Настройки"]
        self.assertEqual([central.tabText(i) for i in range(central.count())], expected_titles)


    def test_main_window_keeps_tab_references_and_refresh_method(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        qt_widgets = importlib.import_module("PySide6.QtWidgets")
        QApplication = qt_widgets.QApplication
        _app = QApplication.instance() or QApplication([])
        from parking_app.ui.main_window import MainWindow

        window = MainWindow()
        self.assertIsNotNone(window.cards_tab)
        self.assertIsNotNone(window.payments_tab)
        self.assertIsNotNone(window.places_tab)
        self.assertTrue(hasattr(window.cards_tab, "cards_changed"))
        self.assertTrue(hasattr(window.cards_tab, "payments_changed"))
        self.assertTrue(hasattr(window.payments_tab, "payments_changed"))
        self.assertTrue(hasattr(window.payments_tab, "refresh_rows"))

        window.cards_tab.refresh_rows = Mock()
        window.payments_tab.refresh_rows = Mock()
        window.places_tab.refresh_rows = Mock()

        window._refresh_payment_dependent_tabs(refresh_payments=True)
        window.cards_tab.refresh_rows.assert_called_once()
        window.places_tab.refresh_rows.assert_called_once()
        window.payments_tab.refresh_rows.assert_called_once()

        window.cards_tab.refresh_rows.reset_mock()
        window.places_tab.refresh_rows.reset_mock()
        window.payments_tab.refresh_rows.reset_mock()

        window._refresh_payment_dependent_tabs(refresh_payments=False)
        window.cards_tab.refresh_rows.assert_called_once()
        window.places_tab.refresh_rows.assert_called_once()
        window.payments_tab.refresh_rows.assert_not_called()

        window.places_tab.refresh_rows.reset_mock()
        window.payments_tab.refresh_rows.reset_mock()
        window._refresh_card_dependent_tabs()
        window.places_tab.refresh_rows.assert_called_once()
        window.payments_tab.refresh_rows.assert_called_once()

    def test_accessible_style_contains_table_contrast_rules(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        qt_widgets = importlib.import_module("PySide6.QtWidgets")
        QApplication = qt_widgets.QApplication
        from parking_app.ui.styles import apply_large_accessible_style

        app = QApplication.instance() or QApplication([])
        apply_large_accessible_style(app)
        ss = app.styleSheet()
        self.assertIn("selection-color", ss)
        self.assertIn("QHeaderView::section", ss)
        self.assertIn("QTableWidget", ss)
        self.assertIn("alternate-background-color", ss)
        self.assertIn("selection-background-color", ss)

    def test_payments_tab_reset_keeps_all_dates_mode(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        qt_widgets = importlib.import_module("PySide6.QtWidgets")
        QApplication = qt_widgets.QApplication
        app = QApplication.instance() or QApplication([])
        from parking_app.ui.payments_tab import PaymentsTab

        tab = PaymentsTab()
        self.assertTrue(hasattr(tab, "export_button"))
        tab._reset_filters()
        self.assertFalse(tab._date_filter_enabled)
        tab._refresh()
        self.assertFalse(tab._date_filter_enabled)


    def test_cards_tab_has_export_button_and_visible_rows(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        qt_widgets = importlib.import_module("PySide6.QtWidgets")
        QApplication = qt_widgets.QApplication
        app = QApplication.instance() or QApplication([])
        from parking_app.ui.cards_tab import CardsTab

        tab = CardsTab()
        self.assertTrue(hasattr(tab, "export_button"))
        self.assertTrue(hasattr(tab, "print_card_button"))
        tab.apply_filters()
        self.assertTrue(hasattr(tab, "_visible_rows"))


    def test_places_tab_has_export_button_and_visible_rows(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        qt_widgets = importlib.import_module("PySide6.QtWidgets")
        QApplication = qt_widgets.QApplication
        _app = QApplication.instance() or QApplication([])
        from parking_app.ui.places_tab import PlacesTab

        tab = PlacesTab()
        self.assertTrue(hasattr(tab, "export_button"))
        tab.apply_filters()
        self.assertTrue(hasattr(tab, "_visible_rows"))

    def test_settings_tab_has_required_controls(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        qt_widgets = importlib.import_module("PySide6.QtWidgets")
        QApplication = qt_widgets.QApplication
        _app = QApplication.instance() or QApplication([])
        from parking_app.ui.settings_tab import SettingsTab

        tab = SettingsTab()
        self.assertTrue(hasattr(tab, "theme_combo"))
        self.assertTrue(hasattr(tab, "warning_days_spin"))
        self.assertTrue(hasattr(tab, "parking_name_edit"))
        self.assertTrue(hasattr(tab, "save_button"))

    def test_main_window_reacts_to_settings_signals(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        qt_widgets = importlib.import_module("PySide6.QtWidgets")
        QApplication = qt_widgets.QApplication
        _app = QApplication.instance() or QApplication([])
        from parking_app.ui.main_window import MainWindow

        window = MainWindow()
        window.cards_tab.refresh_rows = Mock()
        window.places_tab.refresh_rows = Mock()
        window.settings_tab.settings_changed.emit()
        window.cards_tab.refresh_rows.assert_called_once()
        window.places_tab.refresh_rows.assert_called_once()

    def test_close_card_dialog_import_smoke(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        qt_widgets = importlib.import_module("PySide6.QtWidgets")
        QApplication = qt_widgets.QApplication
        _app = QApplication.instance() or QApplication([])
        module = importlib.import_module("parking_app.ui.close_card_dialog")
        self.assertTrue(hasattr(module, "CloseCardDialog"))


if __name__ == "__main__":
    unittest.main()
