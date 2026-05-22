from __future__ import annotations


def resolve_display_place_status(*, has_active_card: bool, manual_status: str) -> str:
    """Resolve displayed place status according to priority rules.

    If active card exists -> occupied regardless of manual status.
    Otherwise use manual status (`free`, `reserved`, `repair`).
    """
    if has_active_card:
        return "occupied"
    return manual_status


def match_place_filter(*, display_status: str, payment_status: str | None, filter_name: str) -> bool:
    """Check whether place row belongs to requested filter."""
    if filter_name == "all":
        return True
    if filter_name == "occupied":
        return display_status == "occupied"
    if filter_name == "free":
        return display_status == "free"
    if filter_name == "reserved":
        return display_status == "reserved"
    if filter_name == "repair":
        return display_status == "repair"
    if filter_name == "overdue":
        return display_status == "occupied" and payment_status == "Просрочено"
    return False
