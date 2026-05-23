from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from sqlalchemy import func, select

from parking_app.database.db import SessionLocal
from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle
from parking_app.repositories.payments_repository import create_payment
from parking_app.services.payment_form_service import format_paid_until, get_next_payment_period, parse_amount_to_kopecks


class PaymentFormDialog(QDialog):
    def __init__(self, parking_card_id: int, parent=None) -> None:
        super().__init__(parent)
        self.parking_card_id = parking_card_id
        self.setWindowTitle("Добавить оплату")
        self.setMinimumSize(760, 620)

        info = self._load_card_info()
        if info is None:
            raise ValueError("PAYMENT_CARD_NOT_FOUND")

        root = QVBoxLayout(self)

        info_group = QGroupBox("Информация по карточке", self)
        info_layout = QVBoxLayout(info_group)
        info_text = (
            f"Клиент: {info['fio']}\n"
            f"Место: {info['place_number']}\n"
            f"Авто: {info['vehicle']} ({info['state_number']})\n"
            f"Оплачено по: {format_paid_until(info['paid_until'])}"
        )
        label = QLabel(info_text, self)
        label.setStyleSheet("font-size: 14pt; line-height: 1.4;")
        info_layout.addWidget(label)
        root.addWidget(info_group)

        form_group = QGroupBox("Данные оплаты", self)
        form = QFormLayout(form_group)
        self.payment_date_edit = QDateEdit(self)
        self.payment_date_edit.setCalendarPopup(True)
        self.payment_date_edit.setDate(QDate.currentDate())

        self.period_from_edit = QDateEdit(self)
        self.period_from_edit.setCalendarPopup(True)
        self.period_to_edit = QDateEdit(self)
        self.period_to_edit.setCalendarPopup(True)

        self.amount_input = QLineEdit(self)
        self.receipt_input = QLineEdit(self)
        self.fiscal_input = QLineEdit(self)
        self.accepted_by_input = QLineEdit(self)
        self.note_input = QTextEdit(self)

        form.addRow("Дата оплаты *", self.payment_date_edit)
        form.addRow("Период с *", self.period_from_edit)
        form.addRow("Период по *", self.period_to_edit)
        form.addRow("Сумма (руб.) *", self.amount_input)
        form.addRow("Номер квитанции", self.receipt_input)
        form.addRow("Фискальный номер", self.fiscal_input)
        form.addRow("Принял оплату", self.accepted_by_input)
        form.addRow("Комментарий", self.note_input)
        root.addWidget(form_group)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Сохранить", self)
        self.cancel_button = QPushButton("Отмена", self)
        buttons.addStretch()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)
        root.addLayout(buttons)

        self.save_button.clicked.connect(self._on_save)
        self.cancel_button.clicked.connect(self.reject)

        if info["card_status"] != "active":
            self.save_button.setEnabled(False)
            QMessageBox.warning(self, "Ошибка", "Оплату можно добавить только к активной карточке.")
        else:
            with SessionLocal() as session:
                period_from, period_to = get_next_payment_period(
                    session, parking_card_id=self.parking_card_id, card_start_date=info["start_date"]
                )
            self.period_from_edit.setDate(QDate(period_from.year, period_from.month, period_from.day))
            self.period_to_edit.setDate(QDate(period_to.year, period_to.month, period_to.day))

    def _load_card_info(self) -> dict | None:
        with SessionLocal() as session:
            paid_until = session.scalar(
                select(func.max(Payment.period_to)).where(Payment.parking_card_id == self.parking_card_id, Payment.status == "active")
            )
            rec = session.execute(
                select(
                    ParkingCard.start_date,
                    ParkingCard.status,
                    ParkingPlace.place_number,
                    Client.surname,
                    Client.name,
                    Client.patronymic,
                    Vehicle.state_number,
                    Vehicle.brand,
                    Vehicle.model,
                )
                .join(ParkingPlace, ParkingPlace.id == ParkingCard.place_id)
                .join(Client, Client.id == ParkingCard.client_id)
                .join(Vehicle, Vehicle.id == ParkingCard.vehicle_id)
                .where(ParkingCard.id == self.parking_card_id)
            ).first()
            if rec is None:
                return None
            fio = " ".join(x for x in [rec.surname, rec.name, rec.patronymic] if x)
            vehicle = " ".join(x for x in [rec.brand, rec.model] if x) or "—"
            return {
                "start_date": rec.start_date,
                "place_number": rec.place_number,
                "fio": fio,
                "state_number": rec.state_number,
                "vehicle": vehicle,
                "paid_until": paid_until,
                "card_status": rec.status,
            }

    def _on_save(self) -> None:
        payment_date = self.payment_date_edit.date().toPython()
        period_from = self.period_from_edit.date().toPython()
        period_to = self.period_to_edit.date().toPython()

        if period_to < period_from:
            QMessageBox.warning(self, "Ошибка", "Дата окончания периода не может быть раньше даты начала.")
            return

        try:
            amount_kopecks = parse_amount_to_kopecks(self.amount_input.text())
        except ValueError as exc:
            mapping = {
                "AMOUNT_REQUIRED": "Введите сумму оплаты.",
                "AMOUNT_INVALID": "Сумма введена некорректно.",
                "AMOUNT_MUST_BE_POSITIVE": "Сумма должна быть больше 0.",
            }
            QMessageBox.warning(self, "Ошибка", mapping.get(str(exc), "Сумма введена некорректно."))
            return

        with SessionLocal() as session:
            try:
                create_payment(
                    session,
                    parking_card_id=self.parking_card_id,
                    payment_date=payment_date,
                    period_from=period_from,
                    period_to=period_to,
                    amount_kopecks=amount_kopecks,
                    receipt_number=self.receipt_input.text().strip() or None,
                    fiscal_number=self.fiscal_input.text().strip() or None,
                    accepted_by=self.accepted_by_input.text().strip() or None,
                    note=self.note_input.toPlainText().strip() or None,
                )
                session.commit()
            except ValueError as exc:
                session.rollback()
                if str(exc) == "PAYMENT_PERIOD_OVERLAP":
                    QMessageBox.warning(self, "Ошибка", "Период оплаты пересекается с уже существующей оплатой.")
                elif str(exc) == "PAYMENT_CARD_NOT_ACTIVE":
                    QMessageBox.warning(self, "Ошибка", "Оплату можно добавить только к активной карточке.")
                elif str(exc) == "PAYMENT_CARD_NOT_FOUND":
                    QMessageBox.warning(self, "Ошибка", "Карточка не найдена. Обновите список карточек.")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось сохранить оплату.")
                return
            except Exception:
                session.rollback()
                QMessageBox.warning(self, "Ошибка", "Неожиданная ошибка при сохранении оплаты.")
                return
        self.accept()
