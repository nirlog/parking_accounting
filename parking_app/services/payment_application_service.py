from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from parking_app.services.payment_service import periods_overlap


@dataclass(frozen=True)
class PaymentValidationError:
    code: str
    message: str


PAYMENT_DATE_REQUIRED = PaymentValidationError("PAYMENT_DATE_REQUIRED", "Укажите дату оплаты.")
PERIOD_FROM_REQUIRED = PaymentValidationError("PERIOD_FROM_REQUIRED", "Укажите дату начала периода оплаты.")
PERIOD_TO_REQUIRED = PaymentValidationError("PERIOD_TO_REQUIRED", "Укажите дату окончания периода оплаты.")
PERIOD_ORDER_INVALID = PaymentValidationError("PERIOD_ORDER_INVALID", "Дата окончания не может быть раньше даты начала.")
PAYMENT_AMOUNT_INVALID = PaymentValidationError("PAYMENT_AMOUNT_INVALID", "Сумма оплаты должна быть больше нуля.")
PAYMENT_PERIOD_OVERLAP = PaymentValidationError(
    "PAYMENT_PERIOD_OVERLAP", "Период оплаты пересекается с уже существующей оплатой."
)


@dataclass(frozen=True)
class PaymentDraft:
    parking_card_id: int
    payment_date: date | None
    period_from: date | None
    period_to: date | None
    amount_kopecks: int


@dataclass(frozen=True)
class PaymentValidationResult:
    ok: bool
    error: PaymentValidationError | None


def validate_payment_draft_fields(draft: PaymentDraft) -> PaymentValidationResult:
    if draft.payment_date is None:
        return PaymentValidationResult(False, PAYMENT_DATE_REQUIRED)
    if draft.period_from is None:
        return PaymentValidationResult(False, PERIOD_FROM_REQUIRED)
    if draft.period_to is None:
        return PaymentValidationResult(False, PERIOD_TO_REQUIRED)
    if draft.period_to < draft.period_from:
        return PaymentValidationResult(False, PERIOD_ORDER_INVALID)
    if draft.amount_kopecks <= 0:
        return PaymentValidationResult(False, PAYMENT_AMOUNT_INVALID)
    return PaymentValidationResult(True, None)


def validate_payment_overlap_in_memory(
    *,
    new_period_from: date,
    new_period_to: date,
    existing_active_periods: list[tuple[date, date]],
) -> PaymentValidationResult:
    for existing_from, existing_to in existing_active_periods:
        if periods_overlap(
            new_period_from=new_period_from,
            new_period_to=new_period_to,
            existing_period_from=existing_from,
            existing_period_to=existing_to,
        ):
            return PaymentValidationResult(False, PAYMENT_PERIOD_OVERLAP)
    return PaymentValidationResult(True, None)


def validate_payment_overlap_with_repo(
    session,
    *,
    parking_card_id: int,
    period_from: date,
    period_to: date,
) -> PaymentValidationResult:
    from parking_app.repositories.payments_repository import has_overlap_with_active_periods

    has_overlap = has_overlap_with_active_periods(
        session,
        parking_card_id=parking_card_id,
        period_from=period_from,
        period_to=period_to,
    )
    if has_overlap:
        return PaymentValidationResult(False, PAYMENT_PERIOD_OVERLAP)
    return PaymentValidationResult(True, None)
