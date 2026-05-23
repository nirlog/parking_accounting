from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from sqlalchemy import func, select

from parking_app.database.db import SessionLocal
from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle
from parking_app.services.card_close_service import calculate_refund_for_active_payments, close_active_card
from parking_app.services.payments_table_service import format_amount_kopecks


class CloseCardDialog(QDialog):
    def __init__(self, card_id: int, parent=None) -> None:
        super().__init__(parent)
        self.card_id = card_id
        self.setWindowTitle("Закрыть карточку")
        self.setMinimumSize(760, 520)

        info = self._load_card_info()
        if info is None:
            raise ValueError("CARD_NOT_FOUND")

        root = QVBoxLayout(self)

        info_group = QGroupBox("Информация по карточке", self)
        info_layout = QVBoxLayout(info_group)
        info_text = (
            f"Клиент: {info['fio']}\n"
            f"Место: {info['place_number']}\n"
            f"Авто: {info['vehicle']} ({info['state_number']})\n"
            f"Оплачено по: {info['paid_until']}"
        )
        self.info_label = QLabel(info_text, self)
        self.info_label.setStyleSheet("font-size: 14pt; line-height: 1.4;")
        info_layout.addWidget(self.info_label)
        root.addWidget(info_group)

        close_group = QGroupBox("Параметры закрытия", self)
        close_layout = QVBoxLayout(close_group)
        row = QHBoxLayout()
        row.addWidget(QLabel("Дата закрытия", self))
        self.closed_at_edit = QDateEdit(self)
        self.closed_at_edit.setCalendarPopup(True)
        today = date.today()
        self.closed_at_edit.setDate(QDate(today.year, today.month, today.day))
        row.addWidget(self.closed_at_edit)
        close_layout.addLayout(row)

        close_layout.addWidget(QLabel("Примечание к возврату", self))
        self.refund_note_edit = QTextEdit(self)
        close_layout.addWidget(self.refund_note_edit)
        root.addWidget(close_group)

        refund_group = QGroupBox("Расчёт возврата", self)
        refund_layout = QVBoxLayout(refund_group)
        self.refund_label = QLabel("", self)
        self.refund_label.setStyleSheet("font-size: 13pt;")
        refund_layout.addWidget(self.refund_label)
        root.addWidget(refund_group)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.close_button = QPushButton("Закрыть карточку", self)
        self.cancel_button = QPushButton("Отмена", self)
        buttons.addWidget(self.close_button)
        buttons.addWidget(self.cancel_button)
        root.addLayout(buttons)

        self.close_button.clicked.connect(self._on_close)
        self.cancel_button.clicked.connect(self.reject)
        self.closed_at_edit.dateChanged.connect(self._update_preview)

        self._update_preview()

    def _load_card_info(self) -> dict | None:
        with SessionLocal() as session:
            paid_until = session.scalar(
                select(func.max(Payment.period_to)).where(Payment.parking_card_id == self.card_id, Payment.status == "active")
            )
            rec = session.execute(
                select(
                    ParkingCard.id,
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
                .where(ParkingCard.id == self.card_id)
            ).first()
            if rec is None:
                return None
            fio = " ".join(x for x in [rec.surname, rec.name, rec.patronymic] if x)
            vehicle = " ".join(x for x in [rec.brand, rec.model] if x) or "—"
            return {
                "status": rec.status,
                "place_number": rec.place_number,
                "fio": fio,
                "state_number": rec.state_number,
                "vehicle": vehicle,
                "paid_until": paid_until.strftime("%d.%m.%Y") if paid_until else "Нет оплат",
            }

    def _update_preview(self) -> None:
        closed_at = self.closed_at_edit.date().toPython()
        with SessionLocal() as session:
            payments = list(
                session.execute(
                select(Payment)
                .where(
                    Payment.parking_card_id == self.card_id,
                    Payment.status == "active",
                    Payment.period_to > closed_at,
                )
                .order_by(Payment.period_from.asc(), Payment.period_to.asc(), Payment.id.asc())
            ).scalars()
            )

        result = calculate_refund_for_active_payments(payments, closed_at=closed_at)
        if result.refund_days > 0:
            self.refund_label.setText(
                "Есть действующий оплаченный период.\n"
                f"Дней к возврату: {result.refund_days}\n"
                f"Сумма к возврату: {format_amount_kopecks(result.refund_amount_kopecks)} руб."
            )
        else:
            self.refund_label.setText("Возврат не требуется.")

    def _on_close(self) -> None:
        closed_at = self.closed_at_edit.date().toPython()
        refund_note = self.refund_note_edit.toPlainText().strip() or None

        with SessionLocal() as session:
            try:
                close_active_card(
                    session,
                    parking_card_id=self.card_id,
                    closed_at=closed_at,
                    refund_note=refund_note,
                )
                session.commit()
                self.accept()
            except ValueError as exc:
                session.rollback()
                if str(exc) == "CARD_NOT_FOUND":
                    QMessageBox.warning(self, "Ошибка", "Карточка не найдена. Обновите список карточек.")
                elif str(exc) == "CARD_NOT_ACTIVE":
                    QMessageBox.warning(self, "Ошибка", "Закрыть можно только активную карточку.")
                else:
                    QMessageBox.warning(self, "Ошибка", "Неожиданная ошибка при закрытии карточки.")
            except Exception:
                session.rollback()
                QMessageBox.warning(self, "Ошибка", "Неожиданная ошибка при закрытии карточки.")
