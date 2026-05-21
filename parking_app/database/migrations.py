from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _table_columns(connection: Connection, table_name: str) -> set[str]:
    rows = connection.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return {str(row["name"]) for row in rows}


def _add_column_if_missing(connection: Connection, table_name: str, column_name: str, ddl: str) -> None:
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
    _add_column_if_missing(connection, "parking_cards", "attendant_name", "VARCHAR(128)")
    _add_column_if_missing(connection, "parking_cards", "note", "TEXT")
    _add_column_if_missing(connection, "parking_cards", "refund_note", "TEXT")
    _add_column_if_missing(connection, "parking_cards", "created_at", "DATETIME")
    _add_column_if_missing(connection, "parking_cards", "updated_at", "DATETIME")

    # payments
    _add_column_if_missing(connection, "payments", "receipt_number", "VARCHAR(64)")
    _add_column_if_missing(connection, "payments", "fiscal_number", "VARCHAR(128)")
    _add_column_if_missing(connection, "payments", "accepted_by", "VARCHAR(128)")
    _add_column_if_missing(connection, "payments", "note", "TEXT")
    _add_column_if_missing(connection, "payments", "created_at", "DATETIME")
    _add_column_if_missing(connection, "payments", "updated_at", "DATETIME")
