from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ConfigTests(unittest.TestCase):
    def test_app_data_dir_can_be_overridden_by_env(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ, {"PARKING_APP_DATA_DIR": td}, clear=False):
                import parking_app.app.config as config

                reloaded = importlib.reload(config)
                self.assertEqual(reloaded.APP_DATA_DIR, Path(td))

    def test_windows_localappdata_used_when_available(self) -> None:
        with patch("platform.system", return_value="Windows"):
            with patch.dict(
                os.environ,
                {"LOCALAPPDATA": r"C:\Users\tester\AppData\Local"},
                clear=True,
            ):
                import parking_app.app.config as config

                reloaded = importlib.reload(config)
                self.assertEqual(
                    reloaded.APP_DATA_DIR,
                    Path(r"C:\Users\tester\AppData\Local") / "ParkingAccounting",
                )

    def test_fallback_user_data_dir_is_not_package_dir(self) -> None:
        with patch("platform.system", return_value="Linux"):
            with patch.dict(os.environ, {}, clear=True):
                import parking_app.app.config as config

                reloaded = importlib.reload(config)
                self.assertNotEqual(reloaded.APP_DATA_DIR, reloaded.BASE_DIR)
                self.assertFalse(str(reloaded.APP_DATA_DIR).startswith(str(reloaded.BASE_DIR)))


if __name__ == "__main__":
    unittest.main()
