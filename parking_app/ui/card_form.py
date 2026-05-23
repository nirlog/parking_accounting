from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from parking_app.database.db import SessionLocal
from parking_app.repositories.cards_repository import next_card_number
from parking_app.services.card_creation_service import CreateCardInput, create_card_with_related


class CardFormDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Добавить карточку")
        self.setMinimumSize(900, 700)

        root = QVBoxLayout(self)
        grid = QGridLayout()

        client_group = QGroupBox("Клиент", self)
        client_form = QFormLayout(client_group)
        self.surname_input = QLineEdit(self)
        self.name_input = QLineEdit(self)
        self.patronymic_input = QLineEdit(self)
        self.phone_input = QLineEdit(self)
        self.document_type_input = QComboBox(self)
        self.document_type_input.addItems(["ВУ", "Паспорт", "Другое"])
        self.document_number_input = QLineEdit(self)
        self.address_input = QTextEdit(self)
        client_form.addRow("Фамилия *", self.surname_input)
        client_form.addRow("Имя *", self.name_input)
        client_form.addRow("Отчество", self.patronymic_input)
        client_form.addRow("Телефон", self.phone_input)
        client_form.addRow("Тип документа", self.document_type_input)
        client_form.addRow("Номер документа", self.document_number_input)
        client_form.addRow("Адрес", self.address_input)

        vehicle_group = QGroupBox("Автомобиль", self)
        vehicle_form = QFormLayout(vehicle_group)
        self.brand_input = QLineEdit(self)
        self.model_input = QLineEdit(self)
        self.color_input = QLineEdit(self)
        self.state_number_input = QLineEdit(self)
        self.vehicle_note_input = QTextEdit(self)
        vehicle_form.addRow("Марка", self.brand_input)
        vehicle_form.addRow("Модель", self.model_input)
        vehicle_form.addRow("Цвет", self.color_input)
        vehicle_form.addRow("Госномер *", self.state_number_input)
        vehicle_form.addRow("Комментарий", self.vehicle_note_input)

        parking_group = QGroupBox("Стоянка", self)
        parking_form = QFormLayout(parking_group)
        self.card_number_input = QLineEdit(self)
        self.paper_card_number_input = QLineEdit(self)
        self.place_number_input = QLineEdit(self)
        self.start_date_input = QDateEdit(self)
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())
        self.attendant_input = QLineEdit(self)
        self.card_note_input = QTextEdit(self)
        parking_form.addRow("Номер карточки *", self.card_number_input)
        parking_form.addRow("Бумажный номер карточки", self.paper_card_number_input)
        parking_form.addRow("Номер места *", self.place_number_input)
        parking_form.addRow("Дата постановки", self.start_date_input)
        parking_form.addRow("Дежурный", self.attendant_input)
        parking_form.addRow("Комментарий", self.card_note_input)

        grid.addWidget(client_group, 0, 0)
        grid.addWidget(vehicle_group, 0, 1)
        grid.addWidget(parking_group, 1, 0, 1, 2)
        root.addLayout(grid)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Сохранить", self)
        self.cancel_button = QPushButton("Отмена", self)
        buttons.addStretch()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)
        root.addLayout(buttons)

        self.save_button.clicked.connect(self._on_save)
        self.cancel_button.clicked.connect(self.reject)

        with SessionLocal() as session:
            self.card_number_input.setText(next_card_number(session))

    def _on_save(self) -> None:
        payload = CreateCardInput(
            surname=self.surname_input.text(),
            name=self.name_input.text(),
            patronymic=self.patronymic_input.text(),
            phone=self.phone_input.text(),
            document_type=self.document_type_input.currentText(),
            document_number=self.document_number_input.text(),
            address=self.address_input.toPlainText(),
            brand=self.brand_input.text(),
            model=self.model_input.text(),
            color=self.color_input.text(),
            state_number=self.state_number_input.text(),
            vehicle_note=self.vehicle_note_input.toPlainText(),
            card_number=self.card_number_input.text(),
            paper_card_number=self.paper_card_number_input.text(),
            place_number=self.place_number_input.text(),
            start_date=self.start_date_input.date().toPython(),
            attendant_name=self.attendant_input.text(),
            card_note=self.card_note_input.toPlainText(),
        )
        with SessionLocal() as session:
            try:
                create_card_with_related(session, payload)
                session.commit()
            except ValueError as exc:
                session.rollback()
                QMessageBox.warning(self, "Ошибка", self._error_text(str(exc)))
                return
            except Exception:
                session.rollback()
                QMessageBox.warning(self, "Ошибка", "Неожиданная ошибка при сохранении карточки.")
                return
        self.accept()

    def _error_text(self, code: str) -> str:
        mapping = {
            "SURNAME_REQUIRED": "Заполните фамилию.",
            "NAME_REQUIRED": "Заполните имя.",
            "STATE_NUMBER_REQUIRED": "Заполните госномер.",
            "PLACE_NUMBER_REQUIRED": "Заполните номер места.",
            "CARD_NUMBER_REQUIRED": "Заполните номер карточки.",
            "PLACE_ALREADY_OCCUPIED": "Это место уже занято другой активной карточкой.",
            "VEHICLE_ALREADY_ACTIVE": "У этого автомобиля уже есть активная карточка.",
            "CARD_NUMBER_ALREADY_EXISTS": "Карточка с таким номером уже существует.",
            "INTEGRITY_ERROR": "Не удалось сохранить карточку из-за ограничения базы данных.",
        }
        return mapping.get(code, "Не удалось сохранить карточку.")
