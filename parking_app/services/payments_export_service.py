from __future__ import annotations

from parking_app.services.export_service import ExportColumn
from parking_app.services.payments_table_service import PaymentTableRow, format_amount_kopecks


def _or_dash(value: str) -> str:
    cleaned = (value or "").strip()
    return cleaned if cleaned else "—"


def _status_text(status: str) -> str:
    if status == "active":
        return "Активная"
    if status == "cancelled":
        return "Отменена"
    return status


def build_payments_export_rows(rows: list[PaymentTableRow]) -> list[dict]:
    export_rows: list[dict] = []
    for row in rows:
        export_rows.append(
            {
                "payment_date": row.payment_date.strftime("%d.%m.%Y"),
                "period_from": row.period_from.strftime("%d.%m.%Y"),
                "period_to": row.period_to.strftime("%d.%m.%Y"),
                "amount": format_amount_kopecks(row.amount_kopecks),
                "fio": _or_dash(row.fio),
                "state_number": _or_dash(row.state_number),
                "place_number": _or_dash(row.place_number),
                "receipt_number": _or_dash(row.receipt_number),
                "fiscal_number": _or_dash(row.fiscal_number),
                "accepted_by": _or_dash(row.accepted_by),
                "status": _status_text(row.status),
                "note": _or_dash(row.note),
            }
        )
    return export_rows


def payments_export_columns() -> list[ExportColumn]:
    return [
        ExportColumn("payment_date", "Дата оплаты"),
        ExportColumn("period_from", "Период с"),
        ExportColumn("period_to", "Период по"),
        ExportColumn("amount", "Сумма"),
        ExportColumn("fio", "ФИО"),
        ExportColumn("state_number", "Госномер"),
        ExportColumn("place_number", "Место"),
        ExportColumn("receipt_number", "Квитанция"),
        ExportColumn("fiscal_number", "Фискальный номер"),
        ExportColumn("accepted_by", "Принял"),
        ExportColumn("status", "Статус"),
        ExportColumn("note", "Комментарий"),
    ]
