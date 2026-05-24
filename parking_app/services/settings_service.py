from __future__ import annotations

from sqlalchemy.orm import Session

from parking_app.repositories.settings_repository import get_setting_value, set_setting_value


DEFAULT_WARNING_DAYS = 3
_ALLOWED_THEME_MODES = {"system", "light", "dark"}


def get_setting(session: Session, key: str, default: str | None = None) -> str | None:
    value = get_setting_value(session, key)
    return default if value is None else value


def set_setting(session: Session, key: str, value: str | None) -> None:
    set_setting_value(session, key, value)


def get_ui_theme_mode(session: Session) -> str:
    raw = (get_setting(session, "ui.theme", "system") or "system").strip().lower()
    return raw if raw in _ALLOWED_THEME_MODES else "system"


def set_ui_theme_mode(session: Session, mode: str) -> None:
    normalized = (mode or "").strip().lower()
    if normalized not in _ALLOWED_THEME_MODES:
        raise ValueError("INVALID_THEME_MODE")
    set_setting(session, "ui.theme", normalized)


def parse_warning_days(raw: str | None, default: int = DEFAULT_WARNING_DAYS) -> int:
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value >= 0 else default


def get_warning_days(session: Session) -> int:
    raw = get_setting(session, "payment_warning_days")
    return parse_warning_days(raw)
