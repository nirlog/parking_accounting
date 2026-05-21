from __future__ import annotations

from importlib.util import find_spec
import subprocess
import sys
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

    def test_main_script_runs_directly(self) -> None:
        proc = subprocess.run([sys.executable, "parking_app/main.py"], capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
