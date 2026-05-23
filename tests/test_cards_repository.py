from __future__ import annotations

from importlib.util import find_spec
import unittest
from datetime import date

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    from parking_app.database.db import Base
    from parking_app.database.models import Client, ParkingCard, ParkingPlace, Vehicle
    from parking_app.repositories.cards_repository import card_number_exists, has_active_card_for_place, has_active_card_for_vehicle, next_card_number


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class CardsRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def _seed_base(self, session: Session) -> tuple[Client, Vehicle, ParkingPlace]:
        client = Client(surname="Иванов", name="Иван", phone="79210000000")
        session.add(client); session.flush()
        vehicle = Vehicle(client_id=client.id, state_number="А111АА178", brand="Lada", model="Vesta")
        place = ParkingPlace(place_number="101", status="free")
        session.add_all([vehicle, place]); session.flush()
        return client, vehicle, place

    def test_db_prevents_second_active_card_for_same_state_number(self) -> None:
        with self.SessionLocal() as session:
            c1, v1, p1 = self._seed_base(session)
            session.add(ParkingCard(card_number="000200", client_id=c1.id, vehicle_id=v1.id, place_id=p1.id, start_date=date(2026, 5, 21), status="active", vehicle_state_number="А111АА178"))
            session.commit()

            c2 = Client(surname="Петров", name="Пётр", phone="79990000000")
            session.add(c2); session.flush()
            v2 = Vehicle(client_id=c2.id, state_number="А111АА178")
            p2 = ParkingPlace(place_number="102", status="free")
            session.add_all([v2, p2]); session.flush()
            session.add(ParkingCard(card_number="000201", client_id=c2.id, vehicle_id=v2.id, place_id=p2.id, start_date=date(2026, 5, 22), status="active", vehicle_state_number="А111АА178"))
            with self.assertRaises(IntegrityError):
                session.commit()

    def test_closed_or_archived_do_not_block_same_state_number(self) -> None:
        with self.SessionLocal() as session:
            c1, v1, p1 = self._seed_base(session)
            card = ParkingCard(card_number="000300", client_id=c1.id, vehicle_id=v1.id, place_id=p1.id, start_date=date(2026, 5, 21), status="active", vehicle_state_number="А111АА178")
            session.add(card); session.commit()
            card.status = "closed"; session.commit()

            c2 = Client(surname="Сидоров", name="Сидор", phone="79990000001")
            session.add(c2); session.flush()
            v2 = Vehicle(client_id=c2.id, state_number="А111АА178")
            p2 = ParkingPlace(place_number="103", status="free")
            session.add_all([v2, p2]); session.flush()
            session.add(ParkingCard(card_number="000301", client_id=c2.id, vehicle_id=v2.id, place_id=p2.id, start_date=date(2026, 5, 22), status="active", vehicle_state_number="А111АА178"))
            session.commit()


if __name__ == "__main__":
    unittest.main()
