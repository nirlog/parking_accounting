from __future__ import annotations

from importlib.util import find_spec
import unittest

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from parking_app.database.db import Base
    from parking_app.repositories.clients_repository import create_client, get_client, list_clients
    from parking_app.repositories.places_repository import create_place, get_place, list_places
    from parking_app.repositories.vehicles_repository import create_vehicle, get_vehicle, list_vehicles_for_client


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class BasicRepositoriesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def test_clients_repository(self) -> None:
        with self.SessionLocal() as session:
            created = create_client(
                session,
                surname="Иванов",
                name="Иван",
                phone="79210000000",
                document_type="Паспорт",
            )
            session.commit()

            loaded = get_client(session, created.id)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.surname, "Иванов")
            self.assertEqual(len(list_clients(session)), 1)

    def test_vehicles_and_places_repositories(self) -> None:
        with self.SessionLocal() as session:
            client = create_client(session, surname="Петров", name="Пётр")
            vehicle = create_vehicle(session, client_id=client.id, state_number="А123АА178", brand="Lada")
            place = create_place(session, place_number="101", status="free")
            session.commit()

            loaded_vehicle = get_vehicle(session, vehicle.id)
            loaded_place = get_place(session, place.id)
            self.assertIsNotNone(loaded_vehicle)
            self.assertIsNotNone(loaded_place)
            self.assertEqual(len(list_vehicles_for_client(session, client.id)), 1)
            self.assertEqual(len(list_places(session)), 1)


if __name__ == "__main__":
    unittest.main()
