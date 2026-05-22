from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlaceViewRow:
    place_number: str
    display_status: str
    client_fio: str
    state_number: str
    paid_until_text: str
    payment_status: str
    note: str


def build_place_view_row(row: dict) -> PlaceViewRow:
    return PlaceViewRow(
        place_number=str(row.get("place_number") or ""),
        display_status=str(row.get("display_status") or ""),
        client_fio=str(row.get("client_fio") or ""),
        state_number=str(row.get("state_number") or ""),
        paid_until_text=str(row.get("paid_until_text") or ""),
        payment_status=str(row.get("payment_status") or ""),
        note=str(row.get("note") or ""),
    )
