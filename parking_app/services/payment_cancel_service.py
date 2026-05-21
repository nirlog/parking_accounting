from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CancelPaymentResult:
    status: str
    cancel_reason: str
    cancelled_at: datetime


def validate_cancel_reason(reason: str) -> bool:
    return bool(reason.strip())


def build_cancel_payment_result(*, reason: str, now: datetime | None = None) -> CancelPaymentResult:
    """Build cancellation payload for soft-cancel workflow."""
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise ValueError("Cancel reason is required")

    return CancelPaymentResult(
        status="cancelled",
        cancel_reason=normalized_reason,
        cancelled_at=now or datetime.now(),
    )
