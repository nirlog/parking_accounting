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
            gridline-color: #c8c8c8;
            alternate-background-color: #f5f7fa;
            font-size: 12pt;
        }

        QTableView::item,
        QTableWidget::item {
            padding: 8px;
        }

        QHeaderView::section {
            min-height: 40px;
            padding: 8px;
            font-size: 12pt;
            font-weight: 600;
            background-color: #e9ecef;
            border: 1px solid #d6d9dd;
        }
        """
    )
