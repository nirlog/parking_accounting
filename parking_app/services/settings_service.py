from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from parking_app.repositories.settings_repository import get_setting_value, set_setting_value


DEFAULT_WARNING_DAYS = 3
_ALLOWED_THEME_MODES = {"system", "light", "dark"}


@dataclass(slots=True)
class ParkingInfo:
    name: str = ""
    address: str = ""
    phone: str = ""
    note: str = ""


@dataclass(slots=True)
class UiFontSettings:
    family: str = "Segoe UI"
    size: int = 13


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


def set_warning_days(session: Session, days: int) -> None:
    if days < 0 or days > 60:
        raise ValueError("INVALID_WARNING_DAYS")
    set_setting(session, "payment_warning_days", str(days))


def get_ui_font_settings(session: Session) -> UiFontSettings:
    family = (get_setting(session, "ui.font_family", "Segoe UI") or "").strip() or "Segoe UI"
    raw_size = get_setting(session, "ui.font_size", "13")
    try:
        size = int(raw_size or "13")
    except (TypeError, ValueError):
        size = 13
    if size < 10 or size > 24:
        size = 13
    return UiFontSettings(family=family, size=size)


def set_ui_font_settings(session: Session, settings: UiFontSettings) -> None:
    size = int(settings.size)
    if size < 10 or size > 24:
        raise ValueError("INVALID_FONT_SIZE")
    family = (settings.family or "").strip() or "Segoe UI"
    set_setting(session, "ui.font_family", family)
    set_setting(session, "ui.font_size", str(size))


def get_parking_info(session: Session) -> ParkingInfo:
    return ParkingInfo(
        name=(get_setting(session, "parking.name", "") or ""),
        address=(get_setting(session, "parking.address", "") or ""),
        phone=(get_setting(session, "parking.phone", "") or ""),
        note=(get_setting(session, "parking.note", "") or ""),
    )


def set_parking_info(session: Session, info: ParkingInfo) -> None:
    set_setting(session, "parking.name", info.name)
    set_setting(session, "parking.address", info.address)
    set_setting(session, "parking.phone", info.phone)
    set_setting(session, "parking.note", info.note)
