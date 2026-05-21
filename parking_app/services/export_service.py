from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class ExportColumn:
    key: str
    header: str


def make_export_filename(report_name: str, now: datetime | None = None) -> str:
    ts = (now or datetime.now()).strftime("%Y-%m-%d_%H%M")
    return f"{report_name}_{ts}.xlsx"


def ensure_unique_export_path(path: Path) -> Path:
    """Return unique path by appending numeric suffix when needed."""
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def format_date_ddmmyyyy(value) -> str:
    if value is None:
        return ""
    return value.strftime("%d.%m.%Y")


def format_amount_rub(kopecks: int | None) -> str:
    if kopecks is None:
        return ""
    rub = (Decimal(kopecks) / Decimal(100)).quantize(Decimal("0.01"))
    return f"{rub:.2f}"


def export_rows_to_xlsx(
    *,
    output_dir: Path,
    report_name: str,
    sheet_name: str,
    columns: list[ExportColumn],
    rows: list[dict],
    now: datetime | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = make_export_filename(report_name, now)
    path = ensure_unique_export_path(output_dir / filename)

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    ws.append([c.header for c in columns])

    if not rows:
        ws.append(["Данные отсутствуют"])
    else:
        for row in rows:
            ws.append([row.get(c.key, "") for c in columns])

    wb.save(path)
    return path
