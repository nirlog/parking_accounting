from __future__ import annotations

import os
from importlib.util import find_spec
import unittest

PYSIDE6_AVAILABLE = find_spec("PySide6") is not None


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 is not installed")
class CardDetailsDialogImportSmokeTests(unittest.TestCase):
    def test_import_dialog_offscreen(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
            from parking_app.ui.card_details_dialog import CardDetailsDialog
        except ImportError as exc:
            self.skipTest(f"Qt runtime unavailable: {exc}")

        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)
        self.assertIsNotNone(CardDetailsDialog)


if __name__ == "__main__":
    unittest.main()
