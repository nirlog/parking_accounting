from __future__ import annotations

from importlib.util import find_spec
import unittest

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from parking_app.main import bootstrap


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class MainBootstrapTests(unittest.TestCase):
    def test_bootstrap_returns_paths(self) -> None:
        info = bootstrap()
        self.assertIn("db_path", info)
        self.assertIn("exports_dir", info)
        self.assertIn("backups_dir", info)


if __name__ == "__main__":
    unittest.main()
