from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from parking_app.services.backup_service import backup_sqlite, make_backup_filename


class BackupServiceTests(unittest.TestCase):
    def test_backup_filename_format(self) -> None:
        name = make_backup_filename(datetime(2026, 5, 21, 9, 45, 30))
        self.assertEqual(name, "parking_backup_2026-05-21_094530_000000.sqlite")

    def test_backup_sqlite_copies_data(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db_path = root / "parking.sqlite"
            backups = root / "backups"

            conn = sqlite3.connect(db_path)
            try:
                conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
                conn.execute("INSERT INTO sample (value) VALUES (?)", ("ok",))
                conn.commit()
            finally:
                conn.close()

            backup_path = backup_sqlite(db_path, backups, now=datetime(2026, 5, 21, 9, 45, 30))
            self.assertTrue(backup_path.exists())

            bconn = sqlite3.connect(backup_path)
            try:
                row = bconn.execute("SELECT value FROM sample WHERE id = 1").fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], "ok")
            finally:
                bconn.close()

    def test_backup_sqlite_raises_when_source_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_db_path = root / "missing.sqlite"
            backups = root / "backups"

            with self.assertRaises(FileNotFoundError):
                backup_sqlite(missing_db_path, backups, now=datetime(2026, 5, 21, 9, 45, 30))


if __name__ == "__main__":
    unittest.main()
