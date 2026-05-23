from __future__ import annotations

from calendar import monthrange
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from parking_app.database.db import SessionLocal
from parking_app.services.payments_table_service import (
    PaymentTableRow,
    build_payment_table_rows,
    calculate_total_amount_kopecks,
    format_amount_kopecks,
)


class PaymentsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[PaymentTableRow] = []
        self._date_filter_enabled = True

        root = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.date_from_edit = QDateEdit(self)
        self.date_from_edit.setCalendarPopup(True)
        self.date_to_edit = QDateEdit(self)
        self.date_to_edit.setCalendarPopup(True)

        self.today_button = QPushButton("Сегодня", self)
        self.month_button = QPushButton("Этот месяц", self)
        self.show_button = QPushButton("Показать", self)
        self.reset_button = QPushButton("Сбросить", self)
        self.refresh_button = QPushButton("Обновить", self)
        self.include_cancelled_cb = QCheckBox("Показывать отменённые", self)

        filters.addWidget(QLabel("Дата с", self))
        filters.addWidget(self.date_from_edit)
        filters.addWidget(QLabel("Дата по", self))
        filters.addWidget(self.date_to_edit)
        filters.addWidget(self.today_button)
        filters.addWidget(self.month_button)
        filters.addWidget(self.show_button)
        filters.addWidget(self.reset_button)
        filters.addWidget(self.refresh_button)
        filters.addWidget(self.include_cancelled_cb)
        root.addLayout(filters)

        self.table = QTableWidget(0, 12, self)
        self.table.setHorizontalHeaderLabels(
            [
                "Дата оплаты",
                "Период с",
                "Период по",
                "Сумма",
                "ФИО",
                "Госномер",
                "Место",
                "Квитанция",
                "Фискальный номер",
                "Принял",
                "Статус",
                "Комментарий",
            ]
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(48)
        root.addWidget(self.table, stretch=1)

        totals = QHBoxLayout()
        self.count_label = QLabel("Количество оплат: 0", self)
        self.sum_label = QLabel("Сумма оплат: 0.00 руб.", self)
        totals.addWidget(self.count_label)
        totals.addStretch()
        totals.addWidget(self.sum_label)
        root.addLayout(totals)

        self.today_button.clicked.connect(self._set_today)
        self.month_button.clicked.connect(self._set_this_month)
        self.show_button.clicked.connect(self._apply_selected_range)
        self.reset_button.clicked.connect(self._reset_filters)
        self.refresh_button.clicked.connect(self._refresh)
        self.include_cancelled_cb.toggled.connect(self._refresh)

        self._set_this_month()

    def _set_qdate(self, widget: QDateEdit, d: date) -> None:
        widget.setDate(d)

    def _set_today(self) -> None:
        today = date.today()
        self._set_qdate(self.date_from_edit, today)
        self._set_qdate(self.date_to_edit, today)
        self._date_filter_enabled = True
        self._refresh()

    def _set_this_month(self) -> None:
        today = date.today()
        first = date(today.year, today.month, 1)
        last = date(today.year, today.month, monthrange(today.year, today.month)[1])
        self._set_qdate(self.date_from_edit, first)
        self._set_qdate(self.date_to_edit, last)
        self._date_filter_enabled = True
        self._refresh()

    def _apply_selected_range(self) -> None:
        self._date_filter_enabled = True
        self._refresh()

    def _reset_filters(self) -> None:
        self._date_filter_enabled = False
        self.date_from_edit.clear()
        self.date_to_edit.clear()
        self._refresh()

    def _refresh(self, *_args) -> None:
        if self._date_filter_enabled:
            date_from = self.date_from_edit.date().toPython()
            date_to = self.date_to_edit.date().toPython()
        else:
            date_from = None
            date_to = None

        if date_from is not None and date_to is not None and date_to < date_from:
            QMessageBox.warning(self, "Ошибка", "Дата окончания периода не может быть раньше даты начала.")
            return

        with SessionLocal() as session:
            self._rows = build_payment_table_rows(
                session,
                date_from=date_from,
                date_to=date_to,
                include_cancelled=self.include_cancelled_cb.isChecked(),
            )
        self._fill_table()

    def _fill_table(self) -> None:
        self.table.setRowCount(0)
        for i, row in enumerate(self._rows):
            self.table.insertRow(i)
            values = [
                row.payment_date.strftime("%d.%m.%Y"),
                row.period_from.strftime("%d.%m.%Y"),
                row.period_to.strftime("%d.%m.%Y"),
                format_amount_kopecks(row.amount_kopecks),
                row.fio,
                row.state_number,
                row.place_number,
                row.receipt_number,
                row.fiscal_number,
                row.accepted_by,
                row.status,
                row.note,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, col, item)

        total = calculate_total_amount_kopecks(self._rows)
        self.count_label.setText(f"Количество оплат: {len(self._rows)}")
        self.sum_label.setText(f"Сумма оплат: {format_amount_kopecks(total)} руб.")
