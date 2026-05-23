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
            conn.execute(text("CREATE TABLE clients (id INTEGER PRIMARY KEY, surname VARCHAR(128), name VARCHAR(128), patronymic VARCHAR(128), phone VARCHAR(32), created_at DATETIME, updated_at DATETIME)"))
            conn.execute(text("CREATE TABLE vehicles (id INTEGER PRIMARY KEY, client_id INTEGER, state_number VARCHAR(32), brand VARCHAR(128), model VARCHAR(128), color VARCHAR(128))"))
            conn.execute(text("CREATE TABLE parking_places (id INTEGER PRIMARY KEY, place_number VARCHAR(32) UNIQUE, status VARCHAR(16), note TEXT)"))
            conn.execute(text("CREATE TABLE parking_cards (id INTEGER PRIMARY KEY, card_number VARCHAR(64) UNIQUE, paper_card_number VARCHAR(64), client_id INTEGER, vehicle_id INTEGER, place_id INTEGER, start_date DATE, closed_at DATE, status VARCHAR(16))"))
            conn.execute(text("CREATE TABLE payments (id INTEGER PRIMARY KEY, parking_card_id INTEGER, payment_date DATE, period_from DATE, period_to DATE, amount_kopecks INTEGER, status VARCHAR(16))"))
            conn.execute(text("CREATE TABLE settings (key VARCHAR(128) PRIMARY KEY, value VARCHAR(512))"))

            apply_mvp_migrations(conn)

            cards_columns = {r["name"] for r in conn.execute(text("PRAGMA table_info(parking_cards)")).mappings().all()}
            self.assertIn("vehicle_state_number", cards_columns)
            indexes = {r["name"] for r in conn.execute(text("PRAGMA index_list(parking_cards)")).mappings().all()}
            self.assertIn("ux_parking_cards_active_state_number", indexes)

    def test_migration_backfills_vehicle_state_number(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE clients (id INTEGER PRIMARY KEY, surname VARCHAR(128), name VARCHAR(128))"))
            conn.execute(text("CREATE TABLE vehicles (id INTEGER PRIMARY KEY, client_id INTEGER, state_number VARCHAR(32))"))
            conn.execute(text("CREATE TABLE parking_places (id INTEGER PRIMARY KEY, place_number VARCHAR(32), status VARCHAR(16))"))
            conn.execute(text("CREATE TABLE parking_cards (id INTEGER PRIMARY KEY, card_number VARCHAR(64), client_id INTEGER, vehicle_id INTEGER, place_id INTEGER, start_date DATE, status VARCHAR(16))"))
            conn.execute(text("CREATE TABLE payments (id INTEGER PRIMARY KEY, parking_card_id INTEGER, payment_date DATE, period_from DATE, period_to DATE, amount_kopecks INTEGER, status VARCHAR(16))"))
            conn.execute(text("INSERT INTO clients(id, surname, name) VALUES (1, 'Иванов', 'Иван')"))
            conn.execute(text("INSERT INTO vehicles(id, client_id, state_number) VALUES (1, 1, 'А123АА178')"))
            conn.execute(text("INSERT INTO parking_places(id, place_number, status) VALUES (1, '101', 'free')"))
            conn.execute(text("INSERT INTO parking_cards(id, card_number, client_id, vehicle_id, place_id, start_date, status) VALUES (1, '000001', 1, 1, 1, '2026-01-01', 'active')"))
            apply_mvp_migrations(conn)
            value = conn.execute(text("SELECT vehicle_state_number FROM parking_cards WHERE id=1")).scalar_one()
            self.assertEqual(value, "А123АА178")


if __name__ == "__main__":
    unittest.main()
