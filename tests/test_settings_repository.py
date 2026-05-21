from __future__ import annotations

from importlib.util import find_spec
import unittest

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from parking_app.database.db import Base
    from parking_app.repositories.settings_repository import get_setting_value, set_setting_value


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class SettingsRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def test_get_set_setting_value(self) -> None:
        with self.SessionLocal() as session:
            self.assertIsNone(get_setting_value(session, "payment_warning_days"))
            set_setting_value(session, "payment_warning_days", "5")
            session.commit()
            self.assertEqual(get_setting_value(session, "payment_warning_days"), "5")

            set_setting_value(session, "payment_warning_days", "7")
            session.commit()
            self.assertEqual(get_setting_value(session, "payment_warning_days"), "7")

    def test_set_setting_value_flushes_for_same_session_read(self) -> None:
        with self.SessionLocal() as session:
            set_setting_value(session, "payment_warning_days", "10")
            self.assertEqual(get_setting_value(session, "payment_warning_days"), "10")


if __name__ == "__main__":
    unittest.main()
