from __future__ import annotations

from pathlib import Path
import unittest


class PyInstallerConfigTests(unittest.TestCase):
    def test_pyinstaller_files_exist(self) -> None:
        self.assertTrue(Path("parking_accounting.spec").exists())
        self.assertTrue(Path("scripts/build_windows.bat").exists())
        self.assertTrue(Path("scripts/build_windows.ps1").exists())
        self.assertTrue(Path("demo/demo_data.json").exists())
        self.assertTrue(Path("scripts/load_demo_data.py").exists())
        self.assertTrue(Path("scripts/load_demo_data.bat").exists())

    def test_spec_contains_expected_markers(self) -> None:
        content = Path("parking_accounting.spec").read_text(encoding="utf-8")
        self.assertIn("ParkingAccounting", content)
        self.assertIn("parking_app", content)
        self.assertIn("main.py", content)

    def test_readme_contains_pyinstaller_instructions(self) -> None:
        content = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("PyInstaller", content)
        self.assertIn("dist\\ParkingAccounting", content)


if __name__ == "__main__":
    unittest.main()
