from __future__ import annotations

from datetime import date, datetime
from html import escape
from pathlib import Path

from parking_app.services.card_details_service import CardDetails, CardPaymentRow
from parking_app.services.export_service import ensure_unique_export_path
from parking_app.services.payments_table_service import format_amount_kopecks


def _fmt_date(value: date | None) -> str:
    return value.strftime("%d.%m.%Y") if value else "—"


def _fmt_text(value: str | None) -> str:
    cleaned = (value or "").strip()
    return cleaned if cleaned else "—"


def _card_status_text(status: str) -> str:
    return {"active": "Активная", "closed": "Закрыта", "archived": "Архив"}.get(status, status)


def _payment_status_text(status: str) -> str:
    return {"active": "Активная", "cancelled": "Отменена"}.get(status, status)


def build_card_print_html(details: CardDetails, payments: list[CardPaymentRow]) -> str:
    paid_until_text = details.paid_until.strftime("%d.%m.%Y") if details.paid_until else "Нет оплат"
    refund_amount_text = f"{format_amount_kopecks(details.refund_amount_kopecks)} руб."

    payments_rows = []
    for p in payments:
        payments_rows.append(
            "<tr>"
            f"<td>{escape(_fmt_date(p.payment_date))}</td>"
            f"<td>{escape(_fmt_date(p.period_from))} — {escape(_fmt_date(p.period_to))}</td>"
            f"<td>{escape(format_amount_kopecks(p.amount_kopecks))}</td>"
            f"<td>{escape(_fmt_text(p.receipt_number))}</td>"
            f"<td>{escape(_fmt_text(p.fiscal_number))}</td>"
            f"<td>{escape(_fmt_text(p.accepted_by))}</td>"
            f"<td>{escape(_payment_status_text(p.status))}</td>"
            f"<td>{escape(_fmt_text(p.note))}</td>"
            "</tr>"
        )

    payments_tbody = "\n".join(payments_rows) or (
        "<tr><td colspan='8'>—</td></tr>"
    )

    return f"""<!DOCTYPE html>
<html lang=\"ru\">
<head>
  <meta charset=\"UTF-8\" />
  <title>Карточка автостоянки</title>
  <style>
    body {{ font-family: Arial, sans-serif; font-size: 14px; color: #111; margin: 24px; }}
    h1 {{ font-size: 24px; margin-bottom: 12px; }}
    h2 {{ font-size: 18px; margin: 18px 0 8px; }}
    .grid {{ display: grid; grid-template-columns: 240px 1fr; gap: 6px 12px; }}
    .label {{ font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border: 1px solid #999; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f0f0f0; }}
  </style>
</head>
<body>
  <h1>Карточка автостоянки</h1>

  <div class=\"grid\">
    <div class=\"label\">Номер карточки:</div><div>{escape(_fmt_text(details.card_number))}</div>
    <div class=\"label\">Бумажный номер:</div><div>{escape(_fmt_text(details.paper_card_number))}</div>
    <div class=\"label\">Статус карточки:</div><div>{escape(_card_status_text(details.card_status))}</div>
    <div class=\"label\">Дата постановки:</div><div>{escape(_fmt_date(details.start_date))}</div>
    <div class=\"label\">Дата закрытия:</div><div>{escape(_fmt_date(details.closed_at))}</div>
    <div class=\"label\">Место:</div><div>{escape(_fmt_text(details.place_number))}</div>
  </div>

  <h2>Клиент</h2>
  <div class=\"grid\">
    <div class=\"label\">ФИО:</div><div>{escape(_fmt_text(details.client_fio))}</div>
    <div class=\"label\">Телефон:</div><div>{escape(_fmt_text(details.phone))}</div>
    <div class=\"label\">Документ:</div><div>{escape(_fmt_text(details.document_type))}</div>
    <div class=\"label\">Номер документа:</div><div>{escape(_fmt_text(details.document_number))}</div>
    <div class=\"label\">Адрес:</div><div>{escape(_fmt_text(details.address))}</div>
  </div>

  <h2>Автомобиль</h2>
  <div class=\"grid\">
    <div class=\"label\">Марка/модель:</div><div>{escape(_fmt_text(details.vehicle_title))}</div>
    <div class=\"label\">Госномер:</div><div>{escape(_fmt_text(details.state_number))}</div>
    <div class=\"label\">Цвет:</div><div>{escape(_fmt_text(details.color))}</div>
  </div>

  <h2>Оплата и возврат</h2>
  <div class=\"grid\">
    <div class=\"label\">Оплачено по:</div><div>{escape(paid_until_text)}</div>
    <div class=\"label\">Статус оплаты:</div><div>{escape(_fmt_text(details.payment_status))}</div>
    <div class=\"label\">Дней возврата:</div><div>{details.refund_days}</div>
    <div class=\"label\">Сумма возврата:</div><div>{escape(refund_amount_text)}</div>
    <div class=\"label\">Примечание к возврату:</div><div>{escape(_fmt_text(details.refund_note))}</div>
  </div>

  <h2>История оплат</h2>
  <table>
    <thead>
      <tr>
        <th>Дата оплаты</th>
        <th>Период</th>
        <th>Сумма</th>
        <th>Квитанция</th>
        <th>Фискальный номер</th>
        <th>Принял</th>
        <th>Статус</th>
        <th>Комментарий</th>
      </tr>
    </thead>
    <tbody>
      {payments_tbody}
    </tbody>
  </table>
</body>
</html>
"""


def export_card_print_html(
    *,
    output_dir: Path,
    details: CardDetails,
    payments: list[CardPaymentRow],
    now: datetime | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = (now or datetime.now()).strftime("%Y-%m-%d_%H%M")
    safe_card_number = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in details.card_number)
    filename = f"card_{safe_card_number}_{ts}.html"
    path = ensure_unique_export_path(output_dir / filename)
    path.write_text(build_card_print_html(details, payments), encoding="utf-8")
    return path
