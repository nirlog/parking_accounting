from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


MIGRATION_DUPLICATE_MARKER = "[migration duplicate active]"


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


def _archive_duplicate_active_cards(connection: Connection, group_column: str, reason: str) -> None:
    note = f"{MIGRATION_DUPLICATE_MARKER} {reason}"
    connection.execute(
        text(
            f"""
            UPDATE parking_cards
            SET
                status = 'archived',
                note = CASE
                    WHEN note IS NULL OR TRIM(note) = '' THEN :note
                    WHEN instr(note, :marker) = 0 THEN note || char(10) || :note
                    ELSE note
                END
            WHERE status = 'active'
              AND id IN (
                SELECT pc.id
                FROM parking_cards pc
                JOIN (
                    SELECT {group_column} AS group_value, MIN(id) AS keep_id
                    FROM parking_cards
                    WHERE status = 'active'
                      AND {group_column} IS NOT NULL
                      AND TRIM(CAST({group_column} AS TEXT)) <> ''
                    GROUP BY {group_column}
                    HAVING COUNT(*) > 1
                ) dup
                    ON pc.{group_column} = dup.group_value
                WHERE pc.id <> dup.keep_id
                  AND pc.status = 'active'
              )
            """
        ),
        {"note": note, "marker": MIGRATION_DUPLICATE_MARKER},
    )


def _archive_active_cards_with_missing_state_number(connection: Connection) -> None:
    note = f"{MIGRATION_DUPLICATE_MARKER} missing vehicle_state_number before active unique indexes"
    connection.execute(
        text(
            """
            UPDATE parking_cards
            SET
                status = 'archived',
                note = CASE
                    WHEN note IS NULL OR TRIM(note) = '' THEN :note
                    WHEN instr(note, :marker) = 0 THEN note || char(10) || :note
                    ELSE note
                END
            WHERE status = 'active'
              AND (vehicle_state_number IS NULL OR TRIM(vehicle_state_number) = '')
            """
        ),
        {"note": note, "marker": MIGRATION_DUPLICATE_MARKER},
    )


def apply_mvp_migrations(connection: Connection) -> None:
    """Apply additive SQLite-safe migrations for schema created by early MVP builds."""
    _add_column_if_missing(connection, "clients", "document_type", "VARCHAR(64)")
    _add_column_if_missing(connection, "clients", "document_number", "VARCHAR(128)")
    _add_column_if_missing(connection, "clients", "address", "VARCHAR(512)")
    _add_column_if_missing(connection, "clients", "photo_path", "VARCHAR(512)")

    _add_column_if_missing(connection, "vehicles", "photo_path", "VARCHAR(512)")
    _add_column_if_missing(connection, "vehicles", "note", "TEXT")
    _add_column_if_missing(connection, "vehicles", "created_at", "DATETIME")
    _add_column_if_missing(connection, "vehicles", "updated_at", "DATETIME")

    _add_column_if_missing(connection, "parking_places", "created_at", "DATETIME")
    _add_column_if_missing(connection, "parking_places", "updated_at", "DATETIME")

    _add_column_if_missing(connection, "parking_cards", "closed_with_active_paid_period", "BOOLEAN DEFAULT 0")
    _add_column_if_missing(connection, "parking_cards", "refund_days", "INTEGER DEFAULT 0")
    _add_column_if_missing(connection, "parking_cards", "refund_amount_kopecks", "INTEGER DEFAULT 0")
    _add_column_if_missing(connection, "parking_cards", "attendant_name", "VARCHAR(128)")
    _add_column_if_missing(connection, "parking_cards", "note", "TEXT")
    _add_column_if_missing(connection, "parking_cards", "refund_note", "TEXT")
    _add_column_if_missing(connection, "parking_cards", "created_at", "DATETIME")
    _add_column_if_missing(connection, "parking_cards", "updated_at", "DATETIME")
    _add_column_if_missing(connection, "parking_cards", "vehicle_state_number", "VARCHAR(32)")

    if _table_exists(connection, "parking_cards") and _table_exists(connection, "vehicles"):
        connection.execute(
            text(
                """
                UPDATE parking_cards
                SET vehicle_state_number = (
                    SELECT vehicles.state_number
                    FROM vehicles
                    WHERE vehicles.id = parking_cards.vehicle_id
                )
                WHERE vehicle_state_number IS NULL
                """
            )
        )

    _add_column_if_missing(connection, "payments", "cancel_reason", "TEXT")
    _add_column_if_missing(connection, "payments", "cancelled_at", "DATETIME")
    _add_column_if_missing(connection, "payments", "receipt_number", "VARCHAR(64)")
    _add_column_if_missing(connection, "payments", "fiscal_number", "VARCHAR(128)")
    _add_column_if_missing(connection, "payments", "accepted_by", "VARCHAR(128)")
    _add_column_if_missing(connection, "payments", "note", "TEXT")
    _add_column_if_missing(connection, "payments", "created_at", "DATETIME")
    _add_column_if_missing(connection, "payments", "updated_at", "DATETIME")

    _add_column_if_missing(connection, "settings", "updated_at", "DATETIME")

    if _table_exists(connection, "parking_cards"):
        _archive_duplicate_active_cards(connection, "place_id", "archived duplicate active card by place_id")
        _archive_duplicate_active_cards(connection, "vehicle_id", "archived duplicate active card by vehicle_id")
        _archive_duplicate_active_cards(
            connection,
            "vehicle_state_number",
            "archived duplicate active card by vehicle_state_number",
        )
        _archive_active_cards_with_missing_state_number(connection)

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

    connection.execute(
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_parking_cards_active_state_number
            ON parking_cards(vehicle_state_number)
            WHERE status = 'active' AND vehicle_state_number IS NOT NULL AND TRIM(vehicle_state_number) <> ''
            """
        )
    )

    connection.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS trg_parking_cards_active_state_number_required_insert
            BEFORE INSERT ON parking_cards
            WHEN NEW.status = 'active'
              AND (NEW.vehicle_state_number IS NULL OR TRIM(NEW.vehicle_state_number) = '')
            BEGIN
                SELECT RAISE(ABORT, 'ACTIVE_CARD_REQUIRES_VEHICLE_STATE_NUMBER');
            END;
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS trg_parking_cards_active_state_number_required_update
            BEFORE UPDATE ON parking_cards
            WHEN NEW.status = 'active'
              AND (NEW.vehicle_state_number IS NULL OR TRIM(NEW.vehicle_state_number) = '')
            BEGIN
                SELECT RAISE(ABORT, 'ACTIVE_CARD_REQUIRES_VEHICLE_STATE_NUMBER');
            END;
            """
        )
    )
