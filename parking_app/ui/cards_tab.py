from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class CardsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(14)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Введите ФИО, номер машины, телефон или номер места")
        self.search_button = QPushButton("Найти", self)
        search_layout.addWidget(self.search_input, stretch=1)
        search_layout.addWidget(self.search_button)
        root_layout.addLayout(search_layout)

        filters_layout = QHBoxLayout()
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        filter_names = [
            "Все активные",
            "Просроченные",
            "Оплата скоро закончится",
            "Нет оплат",
            "Архив",
        ]
        for idx, title in enumerate(filter_names):
            btn = QPushButton(title, self)
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            self.filter_group.addButton(btn)
            filters_layout.addWidget(btn)
        root_layout.addLayout(filters_layout)

        self.table = QTableWidget(0, 8, self)
        self.table.setHorizontalHeaderLabels(
            [
                "Место",
                "ФИО",
                "Госномер",
                "Автомобиль",
                "Телефон",
                "Оплачено по",
                "Статус оплаты",
                "Статус карточки",
            ]
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self._add_placeholder_row()
        root_layout.addWidget(self.table, stretch=1)

        actions_layout = QHBoxLayout()
        action_titles = [
            "Добавить карточку",
            "Открыть карточку",
            "Добавить оплату",
            "Печать карточки",
            "Закрыть карточку",
        ]
        for title in action_titles:
            button = QPushButton(title, self)
            button.clicked.connect(self._show_placeholder_message)
            actions_layout.addWidget(button)
        root_layout.addLayout(actions_layout)

    def _add_placeholder_row(self) -> None:
        self.table.insertRow(0)
        values = [
            "—",
            "Данные появятся после подключения логики",
            "—",
            "—",
            "—",
            "—",
            "—",
            "—",
        ]
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(0, col, item)

    def _show_placeholder_message(self) -> None:
        QMessageBox.information(self, "Информация", "Будет добавлено позже")
