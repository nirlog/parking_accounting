from __future__ import annotations

from parking_app.services.normalization_service import normalize_phone, normalize_state_number


def build_search_text(row: dict) -> str:
    """Build normalized searchable blob for card row.

    Expected fields may include name/phone/state/place/card numbers.
    """
    phone = str(row.get("phone", "") or "").strip()
    state_number = str(row.get("state_number", "") or "").strip()

    parts = [
        row.get("surname", ""),
        row.get("name", ""),
        row.get("patronymic", ""),
        phone,
        normalize_phone(phone),
        state_number,
        normalize_state_number(state_number),
        row.get("place_number", ""),
        row.get("card_number", ""),
        row.get("paper_card_number", ""),
    ]
    return " ".join(str(p).strip().lower() for p in parts if p is not None)


def filter_cards_by_query(rows: list[dict], query: str) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return rows

    candidates = [q]
    phone_q = normalize_phone(q)
    if phone_q:
        candidates.append(phone_q)
    plate_q = normalize_state_number(q)
    if plate_q:
        candidates.append(plate_q.lower())

    return [row for row in rows if any(candidate in build_search_text(row) for candidate in candidates)]
