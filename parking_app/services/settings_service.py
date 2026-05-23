from __future__ import annotations

from parking_app.repositories.settings_repository import get_setting_value


DEFAULT_WARNING_DAYS = 3


def parse_warning_days(raw: str | None, default: int = DEFAULT_WARNING_DAYS) -> int:
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value >= 0 else default


def get_warning_days(session) -> int:
    raw = get_setting_value(session, "payment_warning_days")
    return parse_warning_days(raw)
