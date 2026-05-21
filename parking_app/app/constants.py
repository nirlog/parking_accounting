from __future__ import annotations

from enum import StrEnum


class PaymentStatus(StrEnum):
    NO_PAYMENTS = "Нет оплат"
    OVERDUE = "Просрочено"
    EXPIRING_SOON = "Скоро закончится"
    PAID = "Оплачено"
