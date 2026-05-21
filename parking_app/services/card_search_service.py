from __future__ import annotations


def build_search_text(row: dict) -> str:
    """Build normalized searchable blob for card row.

    Expected fields may include name/phone/state/place/card numbers.
    """
    parts = [
        row.get("surname", ""),
        row.get("name", ""),
        row.get("patronymic", ""),
        row.get("phone", ""),
        row.get("state_number", ""),
        row.get("place_number", ""),
        row.get("card_number", ""),
        row.get("paper_card_number", ""),
    ]
    return " ".join(str(p).strip().lower() for p in parts if p is not None)


def filter_cards_by_query(rows: list[dict], query: str) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return rows
    return [row for row in rows if q in build_search_text(row)]
