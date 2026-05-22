from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from parking_app.database.db import SessionLocal
from parking_app.ui.card_form import CardFormDialog
from parking_app.services.cards_table_service import (
    CardTableRow,
    build_card_table_rows,
    filter_rows_by_quick_filter,
    filter_rows_by_search,
)


class CardsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_rows: list[CardTableRow] = []

        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(14)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Введите ФИО, номер машины, телефон или номер места")
        self.search_button = QPushButton("Найти", self)
        self.refresh_button = QPushButton("Обновить", self)
        search_layout.addWidget(self.search_input, stretch=1)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.refresh_button)
        root_layout.addLayout(search_layout)

        filters_layout = QHBoxLayout()
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        self.filter_names = ["Все активные", "Просроченные", "Оплата скоро закончится", "Нет оплат", "Архив"]
        for idx, title in enumerate(self.filter_names):
            btn = QPushButton(title, self)
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            self.filter_group.addButton(btn)
            filters_layout.addWidget(btn)
        root_layout.addLayout(filters_layout)

        self.table = QTableWidget(0, 8, self)
        self.table.setHorizontalHeaderLabels(
            ["Место", "ФИО", "Госномер", "Автомобиль", "Телефон", "Оплачено по", "Статус оплаты", "Статус карточки"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setDefaultSectionSize(48)
        root_layout.addWidget(self.table, stretch=1)

        actions_layout = QHBoxLayout()
        self.add_card_button = QPushButton("Добавить карточку", self)
        self.add_card_button.clicked.connect(self._open_add_card_dialog)
        actions_layout.addWidget(self.add_card_button)

        for title in ["Открыть карточку", "Добавить оплату", "Печать карточки", "Закрыть карточку"]:
            button = QPushButton(title, self)
            button.clicked.connect(self._show_placeholder_message)
            actions_layout.addWidget(button)
        root_layout.addLayout(actions_layout)

        self.search_button.clicked.connect(self.apply_filters)
        self.search_input.returnPressed.connect(self.apply_filters)
        self.refresh_button.clicked.connect(self.refresh_rows)
        self.filter_group.buttonClicked.connect(self.apply_filters)

        self.refresh_rows()

    def refresh_rows(self) -> None:
        with SessionLocal() as session:
            self._all_rows = build_card_table_rows(session, today=date.today())
        self.apply_filters()

    def apply_filters(self) -> None:
        selected = self.filter_group.checkedButton()
        filter_name = selected.text() if selected is not None else "Все активные"
        filtered = filter_rows_by_quick_filter(self._all_rows, filter_name)
        filtered = filter_rows_by_search(filtered, self.search_input.text())
        self._populate_table(filtered)

    def _populate_table(self, rows: list[CardTableRow]) -> None:
        self.table.setRowCount(0)
        if not rows:
            self.table.setRowCount(1)
            empty_message = "Карточек пока нет" if not self._all_rows else "Нет карточек по выбранным условиям"
            values = ["—", empty_message, "—", "—", "—", "—", "—", "—"]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(0, col, item)
            return

        for row_idx, row in enumerate(rows):
            self.table.insertRow(row_idx)
            paid_until = row.paid_until.strftime("%d.%m.%Y") if row.paid_until is not None else "Нет оплат"
            values = [
                row.place_number,
                row.fio,
                row.state_number,
                row.vehicle,
                row.phone,
                paid_until,
                row.payment_status,
                row.card_status,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col, item)

    def _open_add_card_dialog(self) -> None:
        dialog = CardFormDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_rows()

    def _show_placeholder_message(self) -> None:
        QMessageBox.information(self, "Информация", "Будет добавлено позже")
