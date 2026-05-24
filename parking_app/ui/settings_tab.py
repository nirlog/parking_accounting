from __future__ import annotations

import os
import platform
import subprocess
import webbrowser
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from parking_app.app.config import APP_DATA_DIR, BACKUPS_DIR, DB_PATH, EXPORTS_DIR
from parking_app.database.db import SessionLocal
from parking_app.services.settings_service import (
    ParkingInfo,
    get_parking_info,
    get_ui_theme_mode,
    get_warning_days,
    set_parking_info,
    set_ui_theme_mode,
    set_warning_days,
)


def open_path_in_file_manager(path: Path) -> None:
    if platform.system() == "Windows":
        os.startfile(str(path))  # type: ignore[attr-defined]
        return
    try:
        subprocess.run(["xdg-open", str(path)], check=True)
    except Exception:
        webbrowser.open(path.resolve().as_uri())


class SettingsTab(QWidget):
    theme_changed = Signal(str)
    settings_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)

        title = QLabel("Настройки", self)
        title.setStyleSheet("font-size: 20pt; font-weight: 700;")
        root.addWidget(title)

        ui_group = QGroupBox("Интерфейс", self)
        ui_form = QFormLayout(ui_group)
        self.theme_combo = QComboBox(self)
        self.theme_combo.addItem("Как в Windows", "system")
        self.theme_combo.addItem("Светлая", "light")
        self.theme_combo.addItem("Тёмная", "dark")
        ui_form.addRow("Тема интерфейса", self.theme_combo)

        self.warning_days_spin = QSpinBox(self)
        self.warning_days_spin.setRange(0, 60)
        ui_form.addRow("Предупреждать за N дней до окончания оплаты", self.warning_days_spin)
        root.addWidget(ui_group)

        parking_group = QGroupBox("Данные стоянки", self)
        parking_form = QFormLayout(parking_group)
        self.parking_name_edit = QLineEdit(self)
        self.parking_address_edit = QLineEdit(self)
        self.parking_phone_edit = QLineEdit(self)
        self.parking_note_edit = QTextEdit(self)
        self.parking_note_edit.setMinimumHeight(90)
        parking_form.addRow("Название стоянки", self.parking_name_edit)
        parking_form.addRow("Адрес", self.parking_address_edit)
        parking_form.addRow("Телефон", self.parking_phone_edit)
        parking_form.addRow("Комментарий / реквизиты", self.parking_note_edit)
        root.addWidget(parking_group)

        paths_group = QGroupBox("Папки программы", self)
        paths_layout = QFormLayout(paths_group)
        self.db_path_edit = QLineEdit(str(DB_PATH), self)
        self.db_path_edit.setReadOnly(True)
        self.exports_path_edit = QLineEdit(str(EXPORTS_DIR), self)
        self.exports_path_edit.setReadOnly(True)
        self.backups_path_edit = QLineEdit(str(BACKUPS_DIR), self)
        self.backups_path_edit.setReadOnly(True)
        paths_layout.addRow("База данных", self.db_path_edit)
        paths_layout.addRow("Экспорты", self.exports_path_edit)
        paths_layout.addRow("Бэкапы", self.backups_path_edit)

        btns = QHBoxLayout()
        open_data = QPushButton("Открыть папку данных", self)
        open_data.clicked.connect(lambda: self._open_path(APP_DATA_DIR))
        open_exports = QPushButton("Открыть папку экспортов", self)
        open_exports.clicked.connect(lambda: self._open_path(EXPORTS_DIR))
        open_backups = QPushButton("Открыть папку бэкапов", self)
        open_backups.clicked.connect(lambda: self._open_path(BACKUPS_DIR))
        btns.addWidget(open_data)
        btns.addWidget(open_exports)
        btns.addWidget(open_backups)
        paths_layout.addRow(btns)
        root.addWidget(paths_group)

        actions = QHBoxLayout()
        actions.addStretch()
        self.save_button = QPushButton("Сохранить настройки", self)
        self.save_button.clicked.connect(self._save)
        actions.addWidget(self.save_button)
        root.addLayout(actions)
        root.addStretch()

        self._load()

    def _open_path(self, path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
            open_path_in_file_manager(path)
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть папку.")

    def _load(self) -> None:
        with SessionLocal() as session:
            mode = get_ui_theme_mode(session)
            warning_days = get_warning_days(session)
            info = get_parking_info(session)

        idx = self.theme_combo.findData(mode)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.warning_days_spin.setValue(warning_days)
        self.parking_name_edit.setText(info.name)
        self.parking_address_edit.setText(info.address)
        self.parking_phone_edit.setText(info.phone)
        self.parking_note_edit.setPlainText(info.note)

    def _save(self) -> None:
        mode = str(self.theme_combo.currentData())
        info = ParkingInfo(
            name=self.parking_name_edit.text().strip(),
            address=self.parking_address_edit.text().strip(),
            phone=self.parking_phone_edit.text().strip(),
            note=self.parking_note_edit.toPlainText().strip(),
        )
        try:
            with SessionLocal() as session:
                set_ui_theme_mode(session, mode)
                set_warning_days(session, self.warning_days_spin.value())
                set_parking_info(session, info)
                session.commit()
        except ValueError as exc:
            if str(exc) == "INVALID_THEME_MODE":
                QMessageBox.warning(self, "Ошибка", "Некорректный режим темы.")
            elif str(exc) == "INVALID_WARNING_DAYS":
                QMessageBox.warning(self, "Ошибка", "Некорректное значение дней предупреждения.")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить настройки.")
            return
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить настройки.")
            return

        self.theme_changed.emit(mode)
        self.settings_changed.emit()
        QMessageBox.information(self, "Настройки", "Настройки сохранены.")
