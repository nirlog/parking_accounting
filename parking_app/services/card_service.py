from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str


PLACE_ALREADY_OCCUPIED = ValidationError(
    code="PLACE_ALREADY_OCCUPIED",
    message="Это место уже занято другой активной карточкой.",
)
VEHICLE_ALREADY_ACTIVE = ValidationError(
    code="VEHICLE_ALREADY_ACTIVE",
    message="У этого автомобиля уже есть активная карточка.",
)
CARD_NUMBER_ALREADY_EXISTS = ValidationError(
    code="CARD_NUMBER_ALREADY_EXISTS",
    message="Карточка с таким номером уже существует.",
)


def validate_new_card_constraints(
    *,
    place_has_active_card: bool,
    vehicle_has_active_card: bool,
    card_number_exists: bool,
) -> ValidationError | None:
    """Validate card uniqueness/business constraints in deterministic order."""
    if place_has_active_card:
        return PLACE_ALREADY_OCCUPIED
    if vehicle_has_active_card:
        return VEHICLE_ALREADY_ACTIVE
    if card_number_exists:
        return CARD_NUMBER_ALREADY_EXISTS
    return None
