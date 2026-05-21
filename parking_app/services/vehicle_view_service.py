from __future__ import annotations


def build_vehicle_display(*, brand: str | None, model: str | None, state_number: str) -> str:
    """Return compact vehicle label for UI tables/cards."""
    left = " ".join([p for p in [brand or "", model or ""] if p.strip()]).strip()
    return f"{left}, {state_number}" if left else state_number
