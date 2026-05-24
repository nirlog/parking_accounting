from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from parking_app.database.db import SessionLocal
from parking_app.services.settings_service import get_ui_theme_mode, set_ui_theme_mode
from parking_app.ui.styles import apply_large_accessible_style


class SettingsTab(QWidget):
    theme_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        title = QLabel("Настройки", self)
        title.setStyleSheet("font-size: 20pt; font-weight: 700;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        self.theme_combo = QComboBox(self)
        self.theme_combo.addItem("Как в Windows", "system")
        self.theme_combo.addItem("Светлая", "light")
        self.theme_combo.addItem("Тёмная", "dark")
        form_layout.addRow("Тема интерфейса", self.theme_combo)
        layout.addLayout(form_layout)

        actions = QHBoxLayout()
        actions.addStretch()
        self.apply_button = QPushButton("Применить", self)
        self.apply_button.clicked.connect(self._apply_theme)
        actions.addWidget(self.apply_button)
        layout.addLayout(actions)
        layout.addStretch()

        self._load_theme_value()

    def _load_theme_value(self) -> None:
        with SessionLocal() as session:
            mode = get_ui_theme_mode(session)
        index = self.theme_combo.findData(mode)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

    def _apply_theme(self) -> None:
        mode = str(self.theme_combo.currentData())
        try:
            with SessionLocal() as session:
                set_ui_theme_mode(session, mode)
                session.commit()
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректный режим темы.")
            return
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить настройки темы.")
            return

        app = QApplication.instance()
        if app is not None:
            apply_large_accessible_style(app, theme=mode)
        self.theme_changed.emit(mode)
        QMessageBox.information(self, "Настройки", "Тема применена.")
