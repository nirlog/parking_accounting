from __future__ import annotations

from dataclasses import dataclass

from parking_app.services.card_service import ValidationError, validate_new_card_constraints


@dataclass(frozen=True)
class CreateCardCheckInput:
    place_has_active_card: bool
    vehicle_has_active_card: bool
    card_number_exists: bool


@dataclass(frozen=True)
class CreateCardCheckResult:
    ok: bool
    error: ValidationError | None


def check_create_card_allowed(payload: CreateCardCheckInput) -> CreateCardCheckResult:
    """Application-level wrapper for card creation pre-checks."""
    error = validate_new_card_constraints(
        place_has_active_card=payload.place_has_active_card,
        vehicle_has_active_card=payload.vehicle_has_active_card,
        card_number_exists=payload.card_number_exists,
    )
    return CreateCardCheckResult(ok=error is None, error=error)
