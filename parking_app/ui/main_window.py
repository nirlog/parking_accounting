from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget

from parking_app.ui.cards_tab import CardsTab
from parking_app.ui.payments_tab import PaymentsTab
from parking_app.ui.places_tab import PlacesTab
from parking_app.ui.reports_tab import ReportsTab
from parking_app.ui.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Автостоянка — учёт")
        self.setMinimumSize(1200, 720)

        tabs = QTabWidget(self)
        tabs.addTab(CardsTab(tabs), "Карточки")
        tabs.addTab(PaymentsTab(tabs), "Оплаты")
        tabs.addTab(PlacesTab(tabs), "Места")
        tabs.addTab(ReportsTab(tabs), "Отчёты")
        tabs.addTab(SettingsTab(tabs), "Настройки")

        self.setCentralWidget(tabs)
