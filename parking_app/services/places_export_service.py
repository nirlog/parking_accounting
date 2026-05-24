from __future__ import annotations

from parking_app.services.export_service import ExportColumn
from parking_app.services.places_table_service import PlaceTableRow


_STATUS_TEXT = {
    "free": "Свободно",
    "occupied": "Занято",
    "reserved": "Бронь",
    "repair": "Ремонт",
}


def _or_dash(value: str) -> str:
    cleaned = (value or "").strip()
    return cleaned if cleaned else "—"


def _status_text(status: str) -> str:
    return _STATUS_TEXT.get(status, status)


def _paid_until_text(row: PlaceTableRow) -> str:
    if row.paid_until is not None:
        return row.paid_until.strftime("%d.%m.%Y")
    if row.display_status == "occupied":
        return "Нет оплат"
    return "—"


def build_places_export_rows(rows: list[PlaceTableRow]) -> list[dict]:
    export_rows: list[dict] = []
    for row in rows:
        export_rows.append(
            {
                "place_number": _or_dash(row.place_number),
                "display_status": _status_text(row.display_status),
                "client_fio": _or_dash(row.client_fio),
                "state_number": _or_dash(row.state_number),
                "vehicle": _or_dash(row.vehicle),
                "paid_until": _paid_until_text(row),
                "payment_status": _or_dash(row.payment_status),
                "note": _or_dash(row.note),
            }
        )
    return export_rows


def places_export_columns() -> list[ExportColumn]:
    return [
        ExportColumn("place_number", "Место"),
        ExportColumn("display_status", "Статус"),
        ExportColumn("client_fio", "Клиент"),
        ExportColumn("state_number", "Госномер"),
        ExportColumn("vehicle", "Автомобиль"),
        ExportColumn("paid_until", "Оплачено по"),
        ExportColumn("payment_status", "Статус оплаты"),
        ExportColumn("note", "Примечание"),
    ]
