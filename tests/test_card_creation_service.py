from __future__ import annotations

from datetime import date
from importlib.util import find_spec
import unittest

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import sessionmaker

    from parking_app.database.db import Base
    from parking_app.database.models import Client, ParkingCard, ParkingPlace, Vehicle
    from parking_app.services.card_creation_service import CreateCardInput, create_card_with_related


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class CardCreationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def _payload(self, **overrides):
        data = dict(
            surname="Иванов",
            name="Иван",
            patronymic="Иванович",
            phone="8 (921) 111-22-33",
            document_type="Паспорт",
            document_number="1234 567890",
            address="Адрес",
            brand="Lada",
            model="Vesta",
            color="Белый",
            state_number="A123AA178",
            vehicle_note="",
            card_number="000001",
            paper_card_number="147",
            place_number="101",
            start_date=date(2026, 5, 22),
            attendant_name="Колобков",
            card_note="",
        )
        data.update(overrides)
        return CreateCardInput(**data)

    def test_create_card_with_related_entities_and_normalization(self):
        with self.SessionLocal() as session:
            card = create_card_with_related(session, self._payload())
            session.commit()
            self.assertEqual(card.status, "active")
            self.assertEqual(session.scalar(select(func.count(Client.id))), 1)
            self.assertEqual(session.scalar(select(func.count(Vehicle.id))), 1)
            self.assertEqual(session.scalar(select(func.count(ParkingPlace.id))), 1)
            loaded_client = session.scalar(select(Client))
            loaded_vehicle = session.scalar(select(Vehicle))
            assert loaded_client and loaded_vehicle
            self.assertEqual(loaded_client.phone, "79211112233")
            self.assertEqual(loaded_vehicle.state_number, "А123АА178")

    def test_required_field_errors(self):
        with self.SessionLocal() as session:
            with self.assertRaisesRegex(ValueError, "SURNAME_REQUIRED"):
                create_card_with_related(session, self._payload(surname=" "))
            with self.assertRaisesRegex(ValueError, "NAME_REQUIRED"):
                create_card_with_related(session, self._payload(name=" "))
            with self.assertRaisesRegex(ValueError, "STATE_NUMBER_REQUIRED"):
                create_card_with_related(session, self._payload(state_number=" "))
            with self.assertRaisesRegex(ValueError, "PLACE_NUMBER_REQUIRED"):
                create_card_with_related(session, self._payload(place_number=" "))

    def test_duplicate_card_number_error(self):
        with self.SessionLocal() as session:
            create_card_with_related(session, self._payload(card_number="000001", place_number="101"))
            session.commit()
            with self.assertRaisesRegex(ValueError, "CARD_NUMBER_ALREADY_EXISTS"):
                create_card_with_related(session, self._payload(card_number="000001", place_number="102"))

    def test_occupied_place_error(self):
        with self.SessionLocal() as session:
            create_card_with_related(session, self._payload(card_number="000001", place_number="101"))
            session.commit()
            with self.assertRaisesRegex(ValueError, "PLACE_ALREADY_OCCUPIED"):
                create_card_with_related(session, self._payload(card_number="000002", place_number="101"))

    def test_existing_place_is_reused(self):
        with self.SessionLocal() as session:
            session.add(ParkingPlace(place_number="777", status="free"))
            session.commit()
            before = session.scalar(select(func.count(ParkingPlace.id)))
            create_card_with_related(session, self._payload(card_number="000010", place_number="777"))
            session.commit()
            after = session.scalar(select(func.count(ParkingPlace.id)))
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
