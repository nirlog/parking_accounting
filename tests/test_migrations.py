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
                        status VARCHAR(16),
                        closed_with_active_paid_period BOOLEAN,
                        refund_days INTEGER,
                        refund_amount_kopecks INTEGER
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
                        status VARCHAR(16),
                        cancel_reason TEXT,
                        cancelled_at DATETIME
                    )
                    """
                )
            )

            apply_mvp_migrations(conn)

            columns = conn.execute(text("PRAGMA table_info(payments)")).mappings().all()
            names = {row["name"] for row in columns}
            self.assertIn("receipt_number", names)
            self.assertIn("fiscal_number", names)
            self.assertIn("accepted_by", names)
            self.assertIn("note", names)
            self.assertIn("created_at", names)
            self.assertIn("updated_at", names)


if __name__ == "__main__":
    unittest.main()
