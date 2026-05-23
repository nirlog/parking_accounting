from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


def apply_large_accessible_style(app: QApplication) -> None:
    """Apply high-contrast large UI defaults suitable for older users."""
    font = QFont("Segoe UI", 13)
    app.setFont(font)
    app.setStyleSheet(
        """
        QWidget {
            font-size: 13pt;
        }

        QPushButton {
            min-height: 44px;
            padding: 8px 16px;
            font-size: 13pt;
        }

        QLineEdit,
        QComboBox,
        QDateEdit {
            min-height: 40px;
            padding: 6px 10px;
            font-size: 13pt;
        }

        QTableView,
        QTableWidget {
            background-color: #1f2937;
            alternate-background-color: #273447;
            color: #f9fafb;
            gridline-color: #4b5563;
            selection-background-color: #2d85b3;
            selection-color: #ffffff;
            border: 1px solid #4b5563;
            font-size: 12pt;
        }

        QTableView::item,
        QTableWidget::item {
            padding: 8px;
            color: #f9fafb;
        }

        QHeaderView::section {
            min-height: 40px;
            padding: 8px;
            font-size: 12pt;
            font-weight: 700;
            background-color: #111827;
            color: #f9fafb;
            border: 1px solid #4b5563;
        }
        """
    )
