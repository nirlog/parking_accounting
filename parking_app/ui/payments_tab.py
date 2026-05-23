from __future__ import annotations

from calendar import monthrange
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from parking_app.app.config import EXPORTS_DIR
from parking_app.database.db import SessionLocal
from parking_app.services.export_service import export_rows_to_xlsx
from parking_app.services.payments_export_service import build_payments_export_rows, payments_export_columns
from parking_app.services.payments_table_service import (
    PaymentTableRow,
    build_payment_table_rows,
    calculate_total_amount_kopecks,
    format_amount_kopecks,
)
from parking_app.ui.cancel_payment_dialog import CancelPaymentDialog


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
        self.export_button = QPushButton("Экспорт в Excel", self)
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
        filters.addWidget(self.export_button)
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

        actions = QHBoxLayout()
        self.cancel_payment_button = QPushButton("Отменить оплату", self)
        actions.addStretch()
        actions.addWidget(self.cancel_payment_button)
        root.addLayout(actions)

        self.today_button.clicked.connect(self._set_today)
        self.month_button.clicked.connect(self._set_this_month)
        self.show_button.clicked.connect(self._apply_selected_range)
        self.reset_button.clicked.connect(self._reset_filters)
        self.refresh_button.clicked.connect(self._refresh)
        self.include_cancelled_cb.toggled.connect(self._refresh)
        self.cancel_payment_button.clicked.connect(self._open_cancel_payment_dialog)
        self.export_button.clicked.connect(self._export_to_excel)

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
                "Активная" if row.status == "active" else "Отменена" if row.status == "cancelled" else row.status,
                row.note,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row.payment_id)
                    item.setData(Qt.ItemDataRole.UserRole + 1, row.status)
                self.table.setItem(i, col, item)

        total = calculate_total_amount_kopecks(self._rows)
        self.count_label.setText(f"Количество оплат: {len(self._rows)}")
        self.sum_label.setText(f"Сумма оплат: {format_amount_kopecks(total)} руб.")


    def _export_to_excel(self) -> None:
        if not self._rows:
            QMessageBox.information(self, "Экспорт", "Нет данных для экспорта.")
            return

        try:
            export_rows = build_payments_export_rows(self._rows)
            path = export_rows_to_xlsx(
                output_dir=EXPORTS_DIR,
                report_name="payments",
                sheet_name="Оплаты",
                columns=payments_export_columns(),
                rows=export_rows,
            )
        except Exception:
            QMessageBox.warning(self, "Экспорт", "Не удалось выполнить экспорт оплат.")
            return

        QMessageBox.information(self, "Экспорт", f"Экспорт выполнен: {path}")

    def _open_cancel_payment_dialog(self) -> None:
        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите оплату для отмены.")
            return
        item = self.table.item(row_idx, 0)
        if item is None:
            QMessageBox.warning(self, "Ошибка", "Выберите оплату для отмены.")
            return
        payment_id = item.data(Qt.ItemDataRole.UserRole)
        payment_status = item.data(Qt.ItemDataRole.UserRole + 1)
        if not isinstance(payment_id, int):
            QMessageBox.warning(self, "Ошибка", "Выберите оплату для отмены.")
            return
        if payment_status != "active":
            QMessageBox.warning(self, "Ошибка", "Можно отменить только активную оплату.")
            return

        try:
            dialog = CancelPaymentDialog(payment_id, self)
        except ValueError as exc:
            if str(exc) == "PAYMENT_NOT_FOUND":
                QMessageBox.warning(self, "Ошибка", "Оплата не найдена. Обновите список.")
                return
            raise
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh()
