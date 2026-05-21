from __future__ import annotations

from importlib.util import find_spec
import unittest

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import text

    from parking_app.database.db import engine


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class DbForeignKeysTests(unittest.TestCase):
    def test_sqlite_foreign_keys_enabled(self) -> None:
        with engine.connect() as conn:
            value = conn.execute(text("PRAGMA foreign_keys")).scalar_one()
        self.assertEqual(value, 1)


if __name__ == "__main__":
    unittest.main()
