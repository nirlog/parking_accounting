from __future__ import annotations

from parking_app.services.cards_table_service import CardTableRow
from parking_app.services.export_service import ExportColumn, format_date_ddmmyyyy


def _safe_text(value: str | None) -> str:
    if value is None:
        return "—"
    text = value.strip()
    return text if text else "—"


def _card_status_text(status: str) -> str:
    return {
        "active": "Активная",
        "closed": "Закрыта",
        "archived": "Архив",
    }.get(status, status)


def build_cards_export_rows(rows: list[CardTableRow]) -> list[dict]:
    result: list[dict] = []
    for row in rows:
        result.append(
            {
                "card_number": _safe_text(row.card_number),
                "paper_card_number": _safe_text(row.paper_card_number),
                "place_number": _safe_text(row.place_number),
                "fio": _safe_text(row.fio),
                "state_number": _safe_text(row.state_number),
                "vehicle": _safe_text(row.vehicle),
                "phone": _safe_text(row.phone),
                "paid_until": format_date_ddmmyyyy(row.paid_until) if row.paid_until is not None else "Нет оплат",
                "payment_status": _safe_text(row.payment_status),
                "card_status": _card_status_text(row.card_status),
            }
        )
    return result


def cards_export_columns() -> list[ExportColumn]:
    return [
        ExportColumn("card_number", "Номер карточки"),
        ExportColumn("paper_card_number", "Бумажный номер"),
        ExportColumn("place_number", "Место"),
        ExportColumn("fio", "ФИО"),
        ExportColumn("state_number", "Госномер"),
        ExportColumn("vehicle", "Автомобиль"),
        ExportColumn("phone", "Телефон"),
        ExportColumn("paid_until", "Оплачено по"),
        ExportColumn("payment_status", "Статус оплаты"),
        ExportColumn("card_status", "Статус карточки"),
    ]
