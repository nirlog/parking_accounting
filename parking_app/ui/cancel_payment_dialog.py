from __future__ import annotations

from datetime import UTC, datetime

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from parking_app.database.db import SessionLocal
from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle
from parking_app.services.payment_cancel_service import cancel_active_payment
from parking_app.services.payments_table_service import format_amount_kopecks


class CancelPaymentDialog(QDialog):
    def __init__(self, payment_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.payment_id = payment_id
        self.setWindowTitle("Отменить оплату")
        self.setMinimumSize(650, 420)

        info = self._load_payment_info()
        if info is None:
            raise ValueError("PAYMENT_NOT_FOUND")

        root = QVBoxLayout(self)

        period_text = f"{info['period_from'].strftime('%d.%m.%Y')} — {info['period_to'].strftime('%d.%m.%Y')}"
        info_block = QLabel(
            "\n".join(
                [
                    f"Оплата от: {info['payment_date'].strftime('%d.%m.%Y')}",
                    f"Период: {period_text}",
                    f"Сумма: {format_amount_kopecks(info['amount_kopecks'])} руб.",
                    f"Клиент: {info['client_fio']}",
                    f"Госномер: {info['state_number']}",
                    f"Место: {info['place_number']}",
                    f"Статус: {self._payment_status_ru(info['status'])}",
                ]
            ),
            self,
        )
        info_block.setWordWrap(True)
        root.addWidget(info_block)

        root.addWidget(QLabel("Причина отмены:", self))
        self.reason_edit = QTextEdit(self)
        self.reason_edit.setPlaceholderText("Укажите причину отмены оплаты")
        root.addWidget(self.reason_edit)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.cancel_payment_button = QPushButton("Отменить оплату", self)
        self.close_button = QPushButton("Отмена", self)
        buttons.addWidget(self.cancel_payment_button)
        buttons.addWidget(self.close_button)
        root.addLayout(buttons)

        self.cancel_payment_button.clicked.connect(self._on_cancel_payment)
        self.close_button.clicked.connect(self.reject)

    def _load_payment_info(self):
        with SessionLocal() as session:
            rec = (
                session.query(
                    Payment.id,
                    Payment.payment_date,
                    Payment.period_from,
                    Payment.period_to,
                    Payment.amount_kopecks,
                    Payment.status,
                    Client.surname,
                    Client.name,
                    Client.patronymic,
                    Vehicle.state_number,
                    ParkingPlace.place_number,
                )
                .join(ParkingCard, ParkingCard.id == Payment.parking_card_id)
                .join(Client, Client.id == ParkingCard.client_id)
                .join(Vehicle, Vehicle.id == ParkingCard.vehicle_id)
                .join(ParkingPlace, ParkingPlace.id == ParkingCard.place_id)
                .filter(Payment.id == self.payment_id)
                .one_or_none()
            )
        if rec is None:
            return None
        fio = " ".join(p.strip() for p in [rec.surname, rec.name, rec.patronymic] if p and p.strip()) or "—"
        return {
            "payment_date": rec.payment_date,
            "period_from": rec.period_from,
            "period_to": rec.period_to,
            "amount_kopecks": rec.amount_kopecks,
            "status": rec.status,
            "client_fio": fio,
            "state_number": rec.state_number or "—",
            "place_number": rec.place_number or "—",
        }

    def _on_cancel_payment(self) -> None:
        reason = self.reason_edit.toPlainText().strip()
        if not reason:
            QMessageBox.warning(self, "Ошибка", "Укажите причину отмены оплаты.")
            return

        with SessionLocal() as session:
            try:
                cancel_active_payment(
                    session,
                    payment_id=self.payment_id,
                    cancel_reason=reason,
                    cancelled_at=datetime.now(UTC),
                )
                session.commit()
            except ValueError as exc:
                session.rollback()
                code = str(exc)
                if code == "PAYMENT_NOT_FOUND":
                    QMessageBox.warning(self, "Ошибка", "Оплата не найдена. Обновите список.")
                elif code == "PAYMENT_NOT_ACTIVE":
                    QMessageBox.warning(self, "Ошибка", "Можно отменить только активную оплату.")
                elif code == "PAYMENT_CANCEL_REASON_REQUIRED":
                    QMessageBox.warning(self, "Ошибка", "Укажите причину отмены оплаты.")
                else:
                    QMessageBox.warning(self, "Ошибка", "Неожиданная ошибка при отмене оплаты.")
                return
            except Exception:
                session.rollback()
                QMessageBox.warning(self, "Ошибка", "Неожиданная ошибка при отмене оплаты.")
                return

        self.accept()

    @staticmethod
    def _payment_status_ru(status: str) -> str:
        return {"active": "Активная", "cancelled": "Отменена"}.get(status, status)
