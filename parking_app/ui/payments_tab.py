from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PaymentsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Оплаты", self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24pt; font-weight: 700;")
        text = QLabel("Раздел будет добавлен на следующем этапе", self)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet("font-size: 14pt;")
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(text)
        layout.addStretch()
