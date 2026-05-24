from __future__ import annotations

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from parking_app.ui.cards_tab import CardsTab
from parking_app.ui.payments_tab import PaymentsTab
from parking_app.ui.places_tab import PlacesTab
from parking_app.ui.reports_tab import ReportsTab
from parking_app.ui.settings_tab import SettingsTab
from parking_app.ui.styles import apply_large_accessible_style


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Автостоянка — учёт")
        self.setMinimumSize(1200, 720)

        self.tabs = QTabWidget(self)
        self.cards_tab = CardsTab(self.tabs)
        self.payments_tab = PaymentsTab(self.tabs)
        self.places_tab = PlacesTab(self.tabs)
        self.reports_tab = ReportsTab(self.tabs)
        self.settings_tab = SettingsTab(self.tabs)

        self.tabs.addTab(self.cards_tab, "Карточки")
        self.tabs.addTab(self.payments_tab, "Оплаты")
        self.tabs.addTab(self.places_tab, "Места")
        self.tabs.addTab(self.reports_tab, "Отчёты")
        self.tabs.addTab(self.settings_tab, "Настройки")

        self.cards_tab.cards_changed.connect(self._refresh_card_dependent_tabs)
        self.cards_tab.payments_changed.connect(lambda: self._refresh_payment_dependent_tabs(refresh_payments=True))
        self.payments_tab.payments_changed.connect(lambda: self._refresh_payment_dependent_tabs(refresh_payments=False))
        self.settings_tab.theme_changed.connect(self._apply_theme)
        self.settings_tab.settings_changed.connect(self._refresh_settings_dependent_tabs)

        self.setCentralWidget(self.tabs)

    def _refresh_payment_dependent_tabs(self, *, refresh_payments: bool = True) -> None:
        self.cards_tab.refresh_rows()
        self.places_tab.refresh_rows()
        if refresh_payments:
            self.payments_tab.refresh_rows()

    def _refresh_card_dependent_tabs(self) -> None:
        self.places_tab.refresh_rows()
        self.payments_tab.refresh_rows()

    def _apply_theme(self, theme_mode: str) -> None:
        app = QApplication.instance()
        if app is not None:
            apply_large_accessible_style(app, theme=theme_mode)

    def _refresh_settings_dependent_tabs(self) -> None:
        self.cards_tab.refresh_rows()
        self.places_tab.refresh_rows()
