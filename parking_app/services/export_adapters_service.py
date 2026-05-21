from __future__ import annotations

from parking_app.services.export_service import format_amount_rub, format_date_ddmmyyyy


def map_payment_row_for_export(row: dict) -> dict:
    """Map payment row to export-ready display values."""
    return {
        "payment_date": format_date_ddmmyyyy(row.get("payment_date")),
        "period_from": format_date_ddmmyyyy(row.get("period_from")),
        "period_to": format_date_ddmmyyyy(row.get("period_to")),
        "amount": format_amount_rub(row.get("amount_kopecks")),
        "fio": row.get("fio", ""),
        "state_number": row.get("state_number", ""),
        "place": row.get("place", ""),
        "receipt_number": row.get("receipt_number", ""),
        "fiscal_number": row.get("fiscal_number", ""),
        "accepted_by": row.get("accepted_by", ""),
        "status": row.get("status", ""),
        "cancel_reason": row.get("cancel_reason", ""),
        "note": row.get("note", ""),
    }


def map_payment_rows_for_export(rows: list[dict]) -> list[dict]:
    return [map_payment_row_for_export(r) for r in rows]
