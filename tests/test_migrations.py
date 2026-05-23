from __future__ import annotations

from importlib.util import find_spec
import unittest

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine, text

    from parking_app.database.migrations import apply_mvp_migrations


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class MigrationsTests(unittest.TestCase):
    def _create_old_schema(self, conn) -> None:
        conn.execute(text("CREATE TABLE clients (id INTEGER PRIMARY KEY, surname VARCHAR(128), name VARCHAR(128), patronymic VARCHAR(128), phone VARCHAR(32), created_at DATETIME, updated_at DATETIME)"))
        conn.execute(text("CREATE TABLE vehicles (id INTEGER PRIMARY KEY, client_id INTEGER, state_number VARCHAR(32), brand VARCHAR(128), model VARCHAR(128), color VARCHAR(128))"))
        conn.execute(text("CREATE TABLE parking_places (id INTEGER PRIMARY KEY, place_number VARCHAR(32) UNIQUE, status VARCHAR(16), note TEXT)"))
        conn.execute(text("CREATE TABLE parking_cards (id INTEGER PRIMARY KEY, card_number VARCHAR(64) UNIQUE, paper_card_number VARCHAR(64), client_id INTEGER, vehicle_id INTEGER, place_id INTEGER, start_date DATE, closed_at DATE, status VARCHAR(16))"))
        conn.execute(text("CREATE TABLE payments (id INTEGER PRIMARY KEY, parking_card_id INTEGER, payment_date DATE, period_from DATE, period_to DATE, amount_kopecks INTEGER, status VARCHAR(16))"))
        conn.execute(text("CREATE TABLE settings (key VARCHAR(128) PRIMARY KEY, value VARCHAR(512))"))

    def test_apply_mvp_migrations_adds_missing_columns(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            self._create_old_schema(conn)
            apply_mvp_migrations(conn)

            clients = {r["name"] for r in conn.execute(text("PRAGMA table_info(clients)")).mappings().all()}
            self.assertTrue({"document_type", "document_number", "address", "photo_path"}.issubset(clients))

            vehicles = {r["name"] for r in conn.execute(text("PRAGMA table_info(vehicles)")).mappings().all()}
            self.assertTrue({"photo_path", "note", "created_at", "updated_at"}.issubset(vehicles))

            places = {r["name"] for r in conn.execute(text("PRAGMA table_info(parking_places)")).mappings().all()}
            self.assertTrue({"created_at", "updated_at"}.issubset(places))

            cards = {r["name"] for r in conn.execute(text("PRAGMA table_info(parking_cards)")).mappings().all()}
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
                    "vehicle_state_number",
                }.issubset(cards)
            )

            payments = {r["name"] for r in conn.execute(text("PRAGMA table_info(payments)")).mappings().all()}
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
                }.issubset(payments)
            )

            settings = {r["name"] for r in conn.execute(text("PRAGMA table_info(settings)")).mappings().all()}
            self.assertIn("updated_at", settings)

    def test_apply_mvp_migrations_is_idempotent(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            self._create_old_schema(conn)
            apply_mvp_migrations(conn)
            apply_mvp_migrations(conn)

            payments_cols = [r["name"] for r in conn.execute(text("PRAGMA table_info(payments)")).mappings().all()]
            cards_cols = [r["name"] for r in conn.execute(text("PRAGMA table_info(parking_cards)")).mappings().all()]
            self.assertEqual(payments_cols.count("receipt_number"), 1)
            self.assertEqual(cards_cols.count("vehicle_state_number"), 1)

            indexes = [r["name"] for r in conn.execute(text("PRAGMA index_list(parking_cards)")).mappings().all()]
            self.assertEqual(indexes.count("ux_parking_cards_active_state_number"), 1)

    def test_migration_backfills_vehicle_state_number(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            self._create_old_schema(conn)
            conn.execute(text("INSERT INTO clients(id, surname, name) VALUES (1, 'Иванов', 'Иван')"))
            conn.execute(text("INSERT INTO vehicles(id, client_id, state_number) VALUES (1, 1, 'А123АА178')"))
            conn.execute(text("INSERT INTO parking_places(id, place_number, status) VALUES (1, '101', 'free')"))
            conn.execute(text("INSERT INTO parking_cards(id, card_number, client_id, vehicle_id, place_id, start_date, status) VALUES (1, '000001', 1, 1, 1, '2026-01-01', 'active')"))

            apply_mvp_migrations(conn)
            value = conn.execute(text("SELECT vehicle_state_number FROM parking_cards WHERE id=1")).scalar_one()
            self.assertEqual(value, "А123АА178")

    def test_migration_creates_active_state_number_index(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            self._create_old_schema(conn)
            apply_mvp_migrations(conn)
            indexes = {r["name"] for r in conn.execute(text("PRAGMA index_list(parking_cards)")).mappings().all()}
            self.assertIn("ux_parking_cards_active_state_number", indexes)


    def test_migration_archives_duplicate_active_cards_by_place_before_index(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            self._create_old_schema(conn)
            conn.execute(text("INSERT INTO clients(id, surname, name) VALUES (1,'A','A'),(2,'B','B')"))
            conn.execute(text("INSERT INTO vehicles(id, client_id, state_number) VALUES (1,1,'А1'),(2,2,'А2')"))
            conn.execute(text("INSERT INTO parking_places(id, place_number, status) VALUES (1,'101','free')"))
            conn.execute(text("INSERT INTO parking_cards(id, card_number, client_id, vehicle_id, place_id, start_date, status) VALUES (1,'000001',1,1,1,'2026-01-01','active'), (2,'000002',2,2,1,'2026-01-01','active')"))
            apply_mvp_migrations(conn)
            rows = conn.execute(text("SELECT id,status,note FROM parking_cards ORDER BY id")).mappings().all()
            self.assertEqual(rows[0]['status'],'active')
            self.assertEqual(rows[1]['status'],'archived')
            self.assertIn('[migration duplicate active]', rows[1]['note'])

    def test_migration_archives_duplicate_active_cards_by_vehicle_before_index(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            self._create_old_schema(conn)
            conn.execute(text("INSERT INTO clients(id, surname, name) VALUES (1,'A','A'),(2,'B','B')"))
            conn.execute(text("INSERT INTO vehicles(id, client_id, state_number) VALUES (1,1,'А1')"))
            conn.execute(text("INSERT INTO parking_places(id, place_number, status) VALUES (1,'101','free'),(2,'102','free')"))
            conn.execute(text("INSERT INTO parking_cards(id, card_number, client_id, vehicle_id, place_id, start_date, status) VALUES (1,'000001',1,1,1,'2026-01-01','active'), (2,'000002',2,1,2,'2026-01-01','active')"))
            apply_mvp_migrations(conn)
            statuses = [r['status'] for r in conn.execute(text("SELECT status FROM parking_cards ORDER BY id")).mappings().all()]
            self.assertEqual(statuses, ['active','archived'])

    def test_migration_archives_duplicate_active_cards_by_vehicle_state_number_before_index(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            self._create_old_schema(conn)
            conn.execute(text("INSERT INTO clients(id, surname, name) VALUES (1,'A','A'),(2,'B','B')"))
            conn.execute(text("INSERT INTO vehicles(id, client_id, state_number) VALUES (1,1,'А123АА178'),(2,2,'А123АА178')"))
            conn.execute(text("INSERT INTO parking_places(id, place_number, status) VALUES (1,'101','free'),(2,'102','free')"))
            conn.execute(text("INSERT INTO parking_cards(id, card_number, client_id, vehicle_id, place_id, start_date, status) VALUES (1,'000001',1,1,1,'2026-01-01','active'), (2,'000002',2,2,2,'2026-01-01','active')"))
            apply_mvp_migrations(conn)
            statuses = [r['status'] for r in conn.execute(text("SELECT status FROM parking_cards ORDER BY id")).mappings().all()]
            self.assertEqual(statuses, ['active','archived'])

    def test_migration_archives_active_cards_with_missing_vehicle_state_number(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            self._create_old_schema(conn)
            conn.execute(text("INSERT INTO clients(id, surname, name) VALUES (1,'A','A')"))
            conn.execute(text("INSERT INTO parking_places(id, place_number, status) VALUES (1,'101','free')"))
            conn.execute(text("INSERT INTO parking_cards(id, card_number, client_id, vehicle_id, place_id, start_date, status) VALUES (1,'000001',1,999,1,'2026-01-01','active')"))
            apply_mvp_migrations(conn)
            row = conn.execute(text("SELECT status, note FROM parking_cards WHERE id=1")).mappings().one()
            self.assertEqual(row['status'],'archived')
            self.assertIn('[migration duplicate active]', row['note'])

    def test_migration_duplicate_cleanup_is_idempotent(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        with engine.begin() as conn:
            self._create_old_schema(conn)
            conn.execute(text("INSERT INTO clients(id, surname, name) VALUES (1,'A','A'),(2,'B','B')"))
            conn.execute(text("INSERT INTO vehicles(id, client_id, state_number) VALUES (1,1,'А1'),(2,2,'А1')"))
            conn.execute(text("INSERT INTO parking_places(id, place_number, status) VALUES (1,'101','free'),(2,'102','free')"))
            conn.execute(text("INSERT INTO parking_cards(id, card_number, client_id, vehicle_id, place_id, start_date, status) VALUES (1,'000001',1,1,1,'2026-01-01','active'), (2,'000002',2,2,2,'2026-01-01','active')"))
            apply_mvp_migrations(conn)
            apply_mvp_migrations(conn)
            note = conn.execute(text("SELECT note FROM parking_cards WHERE id=2")).scalar_one()
            self.assertEqual(note.count('[migration duplicate active]'), 1)


if __name__ == "__main__":
    unittest.main()
