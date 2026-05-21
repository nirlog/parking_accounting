from __future__ import annotations


def format_phone_ru(phone_digits: str | None) -> str:
    """Format normalized phone digits to human-readable RU format.

    Expected canonical form: 11 digits starting with 7.
    Falls back to original value when shape is unexpected.
    """
    if not phone_digits:
        return ""

    digits = phone_digits.strip()
    if len(digits) == 11 and digits.startswith("7") and digits.isdigit():
        return f"+7 {digits[1:4]} {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return digits
