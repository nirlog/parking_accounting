from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from parking_app.database.db import SessionLocal
from parking_app.services.places_table_service import (
    PlaceTableRow,
    build_place_table_rows,
    filter_place_rows,
    filter_place_rows_by_search,
)


_STATUS_TEXT = {
    "free": "Свободно",
    "occupied": "Занято",
    "reserved": "Бронь",
    "repair": "Ремонт",
}


class PlacesTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_rows: list[PlaceTableRow] = []

        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(14)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Введите номер места, ФИО, госномер или автомобиль")
        self.search_button = QPushButton("Найти", self)
        self.refresh_button = QPushButton("Обновить", self)
        search_layout.addWidget(self.search_input, stretch=1)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.refresh_button)
        root_layout.addLayout(search_layout)

        filters_layout = QHBoxLayout()
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        self.filter_names = [
            "Все места",
            "Свободные",
            "Занятые",
            "Просроченные",
            "Оплата скоро закончится",
            "Нет оплат",
            "Бронь",
            "Ремонт",
        ]
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
            ["Место", "Статус", "Клиент", "Госномер", "Автомобиль", "Оплачено по", "Статус оплаты", "Примечание"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(48)
        root_layout.addWidget(self.table, stretch=1)

        totals_layout = QHBoxLayout()
        self.total_label = QLabel("Всего мест: 0", self)
        self.free_label = QLabel("Свободно: 0", self)
        self.occupied_label = QLabel("Занято: 0", self)
        self.overdue_label = QLabel("Просрочено: 0", self)
        totals_layout.addWidget(self.total_label)
        totals_layout.addSpacing(12)
        totals_layout.addWidget(self.free_label)
        totals_layout.addSpacing(12)
        totals_layout.addWidget(self.occupied_label)
        totals_layout.addSpacing(12)
        totals_layout.addWidget(self.overdue_label)
        totals_layout.addStretch()
        root_layout.addLayout(totals_layout)

        self.search_button.clicked.connect(self.apply_filters)
        self.search_input.returnPressed.connect(self.apply_filters)
        self.refresh_button.clicked.connect(self.refresh_rows)
        self.filter_group.buttonClicked.connect(self.apply_filters)

        self.refresh_rows()

    def refresh_rows(self) -> None:
        with SessionLocal() as session:
            self._all_rows = build_place_table_rows(session, today=date.today())
        self.apply_filters()

    def apply_filters(self) -> None:
        selected = self.filter_group.checkedButton()
        filter_name = selected.text() if selected is not None else "Все места"
        filtered = filter_place_rows(self._all_rows, filter_name)
        filtered = filter_place_rows_by_search(filtered, self.search_input.text())
        self._populate_table(filtered)
        self._update_totals()

    def _format_paid_until(self, row: PlaceTableRow) -> str:
        if row.paid_until is not None:
            return row.paid_until.strftime("%d.%m.%Y")
        if row.display_status == "occupied":
            return "Нет оплат"
        return "—"

    def _status_text(self, status: str) -> str:
        return _STATUS_TEXT.get(status, status)

    def _populate_table(self, rows: list[PlaceTableRow]) -> None:
        self.table.setRowCount(0)
        if not rows:
            self.table.setRowCount(1)
            message = "Мест пока нет" if not self._all_rows else "Нет мест по выбранным условиям"
            values = ["—", "—", message, "—", "—", "—", "—", "—"]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(0, col, item)
            return

        for i, row in enumerate(rows):
            self.table.insertRow(i)
            values = [
                row.place_number,
                self._status_text(row.display_status),
                row.client_fio,
                row.state_number,
                row.vehicle,
                self._format_paid_until(row),
                row.payment_status,
                row.note,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, col, item)

    def _update_totals(self) -> None:
        total = len(self._all_rows)
        free = sum(1 for r in self._all_rows if r.display_status == "free")
        occupied = sum(1 for r in self._all_rows if r.display_status == "occupied")
        overdue = sum(1 for r in self._all_rows if r.display_status == "occupied" and r.payment_status == "Просрочено")

        self.total_label.setText(f"Всего мест: {total}")
        self.free_label.setText(f"Свободно: {free}")
        self.occupied_label.setText(f"Занято: {occupied}")
        self.overdue_label.setText(f"Просрочено: {overdue}")
