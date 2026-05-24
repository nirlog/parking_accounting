from __future__ import annotations

from importlib.util import find_spec
import os
import unittest

PYSIDE_AVAILABLE = find_spec("PySide6") is not None


@unittest.skipUnless(PYSIDE_AVAILABLE, "PySide6 is not installed")
class CancelPaymentDialogSmokeTests(unittest.TestCase):
    def test_import_dialog_offscreen(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:  # pragma: no cover - environment-specific Qt runtime
            self.skipTest(f"PySide6 runtime is unavailable: {exc}")

        app = QApplication.instance() or QApplication([])
        from parking_app.ui.cancel_payment_dialog import CancelPaymentDialog

        self.assertIsNotNone(CancelPaymentDialog)
        self.assertIsNotNone(app)


if __name__ == "__main__":
    unittest.main()
