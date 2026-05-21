from __future__ import annotations

from importlib.util import find_spec
import unittest

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine, text

    from parking_app.database.migrations import apply_mvp_migrations


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class MigrationsTests(unittest.TestCase):
    def test_apply_mvp_migrations_adds_missing_columns(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE clients (
                        id INTEGER PRIMARY KEY,
                        surname VARCHAR(128) NOT NULL,
                        name VARCHAR(128) NOT NULL,
                        patronymic VARCHAR(128),
                        phone VARCHAR(32),
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE vehicles (
                        id INTEGER PRIMARY KEY,
                        client_id INTEGER NOT NULL,
                        state_number VARCHAR(32) NOT NULL,
                        brand VARCHAR(128),
                        model VARCHAR(128),
                        color VARCHAR(128)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE parking_places (id INTEGER PRIMARY KEY, place_number VARCHAR(32) UNIQUE, status VARCHAR(16), note TEXT)"
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE parking_cards (
                        id INTEGER PRIMARY KEY,
                        card_number VARCHAR(64) UNIQUE,
                        paper_card_number VARCHAR(64),
                        client_id INTEGER,
                        vehicle_id INTEGER,
                        place_id INTEGER,
                        start_date DATE,
                        closed_at DATE,
                        status VARCHAR(16)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE payments (
                        id INTEGER PRIMARY KEY,
                        parking_card_id INTEGER,
                        payment_date DATE,
                        period_from DATE,
                        period_to DATE,
                        amount_kopecks INTEGER,
                        status VARCHAR(16)
                    )
                    """
                )
            )
            conn.execute(text("CREATE TABLE settings (key VARCHAR(128) PRIMARY KEY, value VARCHAR(512))"))

            apply_mvp_migrations(conn)

            clients_columns = {row["name"] for row in conn.execute(text("PRAGMA table_info(clients)")).mappings().all()}
            self.assertTrue({"document_type", "document_number", "address", "photo_path"}.issubset(clients_columns))

            vehicles_columns = {
                row["name"] for row in conn.execute(text("PRAGMA table_info(vehicles)")).mappings().all()
            }
            self.assertTrue({"photo_path", "note", "created_at", "updated_at"}.issubset(vehicles_columns))

            places_columns = {
                row["name"] for row in conn.execute(text("PRAGMA table_info(parking_places)")).mappings().all()
            }
            self.assertTrue({"created_at", "updated_at"}.issubset(places_columns))

            cards_columns = {
                row["name"] for row in conn.execute(text("PRAGMA table_info(parking_cards)")).mappings().all()
            }
            self.assertTrue(
                {
                    "closed_with_active_paid_period",
                    "refund_days",
                    "refund_amount_kopecks",
                    "attendant_name",
                    "note",
                    "refund_note",
                    "created_at",
                    "updated_at",
                }.issubset(cards_columns)
            )

            payments_columns = {row["name"] for row in conn.execute(text("PRAGMA table_info(payments)")).mappings().all()}
            self.assertTrue(
                {
                    "cancel_reason",
                    "cancelled_at",
                    "receipt_number",
                    "fiscal_number",
                    "accepted_by",
                    "note",
                    "created_at",
                    "updated_at",
                }.issubset(
                    payments_columns
                )
            )

            settings_columns = {row["name"] for row in conn.execute(text("PRAGMA table_info(settings)")).mappings().all()}
            self.assertIn("updated_at", settings_columns)

    def test_apply_mvp_migrations_is_idempotent(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE clients (
                        id INTEGER PRIMARY KEY,
                        surname VARCHAR(128) NOT NULL,
                        name VARCHAR(128) NOT NULL,
                        patronymic VARCHAR(128),
                        phone VARCHAR(32),
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE vehicles (id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL, state_number VARCHAR(32) NOT NULL)"
                )
            )
            conn.execute(
                text("CREATE TABLE parking_places (id INTEGER PRIMARY KEY, place_number VARCHAR(32) UNIQUE, status VARCHAR(16))")
            )
            conn.execute(
                text(
                    "CREATE TABLE parking_cards (id INTEGER PRIMARY KEY, card_number VARCHAR(64) UNIQUE, client_id INTEGER, vehicle_id INTEGER, place_id INTEGER, start_date DATE, status VARCHAR(16))"
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE payments (id INTEGER PRIMARY KEY, parking_card_id INTEGER, payment_date DATE, period_from DATE, period_to DATE, amount_kopecks INTEGER, status VARCHAR(16))"
                )
            )

            apply_mvp_migrations(conn)
            apply_mvp_migrations(conn)

            payments_columns = conn.execute(text("PRAGMA table_info(payments)")).mappings().all()
            payments_names = [row["name"] for row in payments_columns]
            self.assertEqual(payments_names.count("receipt_number"), 1)


if __name__ == "__main__":
    unittest.main()
