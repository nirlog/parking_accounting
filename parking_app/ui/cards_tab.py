from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, Signal
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
from parking_app.ui.close_card_dialog import CloseCardDialog
from parking_app.ui.card_details_dialog import CardDetailsDialog
from parking_app.ui.payment_form import PaymentFormDialog
from parking_app.services.cards_table_service import (
    CardTableRow,
    build_card_table_rows,
    filter_rows_by_quick_filter,
    filter_rows_by_search,
)


class CardsTab(QWidget):
    cards_changed = Signal()
    payments_changed = Signal()

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
        self.filter_names = ["Все активные", "Просроченные", "Оплата скоро закончится", "Нет оплат", "Закрытые", "Архив"]
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

        self.open_card_button = QPushButton("Открыть карточку", self)
        self.open_card_button.clicked.connect(self._open_card_details_dialog)
        actions_layout.addWidget(self.open_card_button)

        self.add_payment_button = QPushButton("Добавить оплату", self)
        self.add_payment_button.clicked.connect(self._open_add_payment_dialog)
        actions_layout.addWidget(self.add_payment_button)

        print_button = QPushButton("Печать карточки", self)
        print_button.clicked.connect(self._show_placeholder_message)
        actions_layout.addWidget(print_button)

        self.close_card_button = QPushButton("Закрыть карточку", self)
        self.close_card_button.clicked.connect(self._open_close_card_dialog)
        actions_layout.addWidget(self.close_card_button)
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
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row.card_id)
                    item.setData(Qt.ItemDataRole.UserRole + 1, row.card_status)
                self.table.setItem(row_idx, col, item)

    def _open_add_card_dialog(self) -> None:
        dialog = CardFormDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_rows()
            self.cards_changed.emit()


    def _open_card_details_dialog(self) -> None:
        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите карточку для открытия.")
            return
        first_item = self.table.item(row_idx, 0)
        if first_item is None:
            QMessageBox.warning(self, "Ошибка", "Выберите карточку для открытия.")
            return
        card_id = first_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(card_id, int):
            QMessageBox.warning(self, "Ошибка", "Выберите карточку для открытия.")
            return
        try:
            dialog = CardDetailsDialog(card_id, self)
        except ValueError as exc:
            if str(exc) == "CARD_NOT_FOUND":
                QMessageBox.warning(self, "Ошибка", "Карточка не найдена. Обновите список карточек.")
                return
            raise
        dialog.exec()

    def _open_add_payment_dialog(self) -> None:
        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите карточку для добавления оплаты.")
            return
        first_item = self.table.item(row_idx, 0)
        if first_item is None:
            QMessageBox.warning(self, "Ошибка", "Выберите карточку для добавления оплаты.")
            return
        card_id = first_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(card_id, int):
            QMessageBox.warning(self, "Ошибка", "Выберите карточку для добавления оплаты.")
            return
        card_status = first_item.data(Qt.ItemDataRole.UserRole + 1)
        if card_status != "active":
            QMessageBox.warning(self, "Ошибка", "Оплату можно добавить только к активной карточке.")
            return

        try:
            dialog = PaymentFormDialog(card_id, self)
        except ValueError as exc:
            if str(exc) == "PAYMENT_CARD_NOT_FOUND":
                QMessageBox.warning(self, "Ошибка", "Карточка не найдена. Обновите список карточек.")
                return
            raise
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_rows()
            self.payments_changed.emit()

    def _open_close_card_dialog(self) -> None:
        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите карточку для закрытия.")
            return
        first_item = self.table.item(row_idx, 0)
        if first_item is None:
            QMessageBox.warning(self, "Ошибка", "Выберите карточку для закрытия.")
            return
        card_id = first_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(card_id, int):
            QMessageBox.warning(self, "Ошибка", "Выберите карточку для закрытия.")
            return
        card_status = first_item.data(Qt.ItemDataRole.UserRole + 1)
        if card_status != "active":
            QMessageBox.warning(self, "Ошибка", "Закрыть можно только активную карточку.")
            return

        try:
            dialog = CloseCardDialog(card_id, self)
        except ValueError as exc:
            if str(exc) == "CARD_NOT_FOUND":
                QMessageBox.warning(self, "Ошибка", "Карточка не найдена. Обновите список карточек.")
                return
            raise
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_rows()
            self.cards_changed.emit()

    def _show_placeholder_message(self) -> None:
        QMessageBox.information(self, "Информация", "Будет добавлено позже")
