from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from parking_app.database.models import Setting


def get_setting_value(session: Session, key: str) -> str | None:
    value = session.scalar(select(Setting.value).where(Setting.key == key))
    return value if value is not None else None


def set_setting_value(session: Session, key: str, value: str | None) -> None:
    setting = session.get(Setting, key)
    if setting is None:
        session.add(Setting(key=key, value=value))
    else:
        setting.value = value
    session.flush()
