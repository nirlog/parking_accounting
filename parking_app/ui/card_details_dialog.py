from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from parking_app.database.db import SessionLocal
from parking_app.services.card_details_service import get_card_details
from parking_app.services.payments_table_service import format_amount_kopecks


def _fmt_date(d: date | None) -> str:
    return d.strftime("%d.%m.%Y") if d else "—"


def _card_status(v: str) -> str:
    return {"active": "Активная", "closed": "Закрыта", "archived": "Архив"}.get(v, v)


def _pay_status(v: str) -> str:
    return {"active": "Активная", "cancelled": "Отменена"}.get(v, v)


class CardDetailsDialog(QDialog):
    def __init__(self, parking_card_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Карточка")
        self.setMinimumSize(900, 700)

        with SessionLocal() as session:
            details, payments = get_card_details(session, parking_card_id=parking_card_id, today=date.today())

        root = QVBoxLayout(self)
        header = QGroupBox("Основная информация", self)
        hf = QFormLayout(header)
        hf.addRow("Номер карточки:", QLabel(details.card_number))
        hf.addRow("Статус карточки:", QLabel(_card_status(details.card_status)))
        hf.addRow("Место:", QLabel(details.place_number))
        hf.addRow("Госномер:", QLabel(details.state_number))
        hf.addRow("ФИО:", QLabel(details.client_fio))
        hf.addRow("Оплачено по:", QLabel(_fmt_date(details.paid_until) if details.paid_until else "Нет оплат"))
        hf.addRow("Статус оплаты:", QLabel(details.payment_status))
        root.addWidget(header)

        tabs = QTabWidget(self)
        root.addWidget(tabs, 1)

        client_w = QWidget(self)
        cf = QFormLayout(client_w)
        cf.addRow("ФИО:", QLabel(details.client_fio))
        cf.addRow("Телефон:", QLabel(details.phone))
        cf.addRow("Документ:", QLabel(details.document_type))
        cf.addRow("Номер документа:", QLabel(details.document_number))
        cf.addRow("Адрес:", QLabel(details.address))
        tabs.addTab(client_w, "Клиент")

        vehicle_w = QWidget(self)
        vf = QFormLayout(vehicle_w)
        vf.addRow("Марка/модель:", QLabel(details.vehicle_title))
        vf.addRow("Госномер:", QLabel(details.state_number))
        vf.addRow("Цвет:", QLabel(details.color))
        vf.addRow("Комментарий:", QLabel(details.vehicle_note))
        tabs.addTab(vehicle_w, "Автомобиль")

        parking_w = QWidget(self)
        pf = QFormLayout(parking_w)
        pf.addRow("Номер карточки:", QLabel(details.card_number))
        pf.addRow("Бумажный номер:", QLabel(details.paper_card_number or "—"))
        pf.addRow("Место:", QLabel(details.place_number))
        pf.addRow("Дата постановки:", QLabel(_fmt_date(details.start_date)))
        pf.addRow("Дата закрытия:", QLabel(_fmt_date(details.closed_at)))
        pf.addRow("Дежурный:", QLabel(details.attendant_name))
        pf.addRow("Комментарий:", QLabel(details.card_note))
        pf.addRow("Дней возврата:", QLabel(str(details.refund_days)))
        pf.addRow("Сумма возврата:", QLabel(f"{format_amount_kopecks(details.refund_amount_kopecks)} руб."))
        pf.addRow("Примечание к возврату:", QLabel(details.refund_note))
        tabs.addTab(parking_w, "Стоянка")

        payments_w = QWidget(self)
        pv = QVBoxLayout(payments_w)
        table = QTableWidget(0, 9, self)
        table.setHorizontalHeaderLabels([
            "Дата оплаты", "Период с", "Период по", "Сумма", "Квитанция", "Фискальный номер", "Принял", "Статус", "Комментарий"
        ])
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setDefaultSectionSize(44)
        for r, p in enumerate(payments):
            table.insertRow(r)
            vals = [
                _fmt_date(p.payment_date), _fmt_date(p.period_from), _fmt_date(p.period_to),
                format_amount_kopecks(p.amount_kopecks), p.receipt_number, p.fiscal_number,
                p.accepted_by, _pay_status(p.status), p.note,
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, it)
        pv.addWidget(table)
        tabs.addTab(payments_w, "Оплаты")
