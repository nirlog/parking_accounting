from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _table_columns(connection: Connection, table_name: str) -> set[str]:
    rows = connection.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return {str(row["name"]) for row in rows}


def _table_exists(connection: Connection, table_name: str) -> bool:
    row = connection.execute(
        text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:table_name"),
        {"table_name": table_name},
    ).first()
    return row is not None


def _add_column_if_missing(connection: Connection, table_name: str, column_name: str, ddl: str) -> None:
    if not _table_exists(connection, table_name):
        return
    if column_name in _table_columns(connection, table_name):
        return
    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))


def apply_mvp_migrations(connection: Connection) -> None:
    """Apply additive SQLite-safe migrations for schema created by early MVP builds."""
    # clients
    _add_column_if_missing(connection, "clients", "document_type", "VARCHAR(64)")
    _add_column_if_missing(connection, "clients", "document_number", "VARCHAR(128)")
    _add_column_if_missing(connection, "clients", "address", "VARCHAR(512)")
    _add_column_if_missing(connection, "clients", "photo_path", "VARCHAR(512)")

    # vehicles
    _add_column_if_missing(connection, "vehicles", "photo_path", "VARCHAR(512)")
    _add_column_if_missing(connection, "vehicles", "note", "TEXT")
    _add_column_if_missing(connection, "vehicles", "created_at", "DATETIME")
    _add_column_if_missing(connection, "vehicles", "updated_at", "DATETIME")

    # parking_places
    _add_column_if_missing(connection, "parking_places", "created_at", "DATETIME")
    _add_column_if_missing(connection, "parking_places", "updated_at", "DATETIME")

    # parking_cards
    _add_column_if_missing(connection, "parking_cards", "closed_with_active_paid_period", "BOOLEAN DEFAULT 0")
    _add_column_if_missing(connection, "parking_cards", "refund_days", "INTEGER DEFAULT 0")
    _add_column_if_missing(connection, "parking_cards", "refund_amount_kopecks", "INTEGER DEFAULT 0")
    _add_column_if_missing(connection, "parking_cards", "attendant_name", "VARCHAR(128)")
    _add_column_if_missing(connection, "parking_cards", "note", "TEXT")
    _add_column_if_missing(connection, "parking_cards", "refund_note", "TEXT")
    _add_column_if_missing(connection, "parking_cards", "created_at", "DATETIME")
    _add_column_if_missing(connection, "parking_cards", "updated_at", "DATETIME")

    # payments
    _add_column_if_missing(connection, "payments", "cancel_reason", "TEXT")
    _add_column_if_missing(connection, "payments", "cancelled_at", "DATETIME")
    _add_column_if_missing(connection, "payments", "receipt_number", "VARCHAR(64)")
    _add_column_if_missing(connection, "payments", "fiscal_number", "VARCHAR(128)")
    _add_column_if_missing(connection, "payments", "accepted_by", "VARCHAR(128)")
    _add_column_if_missing(connection, "payments", "note", "TEXT")
    _add_column_if_missing(connection, "payments", "created_at", "DATETIME")
    _add_column_if_missing(connection, "payments", "updated_at", "DATETIME")

    # settings
    _add_column_if_missing(connection, "settings", "updated_at", "DATETIME")

    # active card uniqueness indexes
    connection.execute(
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_parking_cards_active_place
            ON parking_cards(place_id)
            WHERE status = 'active'
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_parking_cards_active_vehicle
            ON parking_cards(vehicle_id)
            WHERE status = 'active'
            """
        )
    )
