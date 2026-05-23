from __future__ import annotations


def normalize_card_number(raw: str) -> str:
    """Normalize card number by trimming spaces.

    Keeps leading zeros intact.
    """
    return raw.strip()


def validate_card_number_required(raw: str) -> bool:
    return bool(normalize_card_number(raw))
