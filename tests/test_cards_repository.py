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
    from parking_app.repositories.cards_repository import (
        card_number_exists,
        has_active_card_for_place,
        has_active_card_for_vehicle,
        next_card_number,
    )


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class CardsRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def _seed_base(self, session: Session) -> tuple[Client, Vehicle, ParkingPlace]:
        client = Client(surname="Иванов", name="Иван", patronymic=None, phone="79210000000")
        session.add(client)
        session.flush()

        vehicle = Vehicle(client_id=client.id, state_number="А111АА178", brand="Lada", model="Vesta", color=None)
        place = ParkingPlace(place_number="101", status="free", note=None)
        session.add_all([vehicle, place])
        session.flush()
        return client, vehicle, place

    def test_active_place_and_vehicle_detection(self) -> None:
        with self.SessionLocal() as session:
            _, vehicle, place = self._seed_base(session)
            session.add(
                ParkingCard(
                    card_number="000001",
                    paper_card_number="101",
                    client_id=1,
                    vehicle_id=vehicle.id,
                    place_id=place.id,
                    start_date=date(2026, 5, 21),
                    closed_at=None,
                    status="active",
                )
            )
            session.commit()

            self.assertTrue(has_active_card_for_place(session, place.id))
            self.assertTrue(has_active_card_for_vehicle(session, vehicle.id))

    def test_non_active_cards_ignored(self) -> None:
        with self.SessionLocal() as session:
            _, vehicle, place = self._seed_base(session)
            session.add(
                ParkingCard(
                    card_number="000001",
                    paper_card_number=None,
                    client_id=1,
                    vehicle_id=vehicle.id,
                    place_id=place.id,
                    start_date=date(2026, 5, 21),
                    closed_at=date(2026, 5, 22),
                    status="closed",
                )
            )
            session.commit()

            self.assertFalse(has_active_card_for_place(session, place.id))
            self.assertFalse(has_active_card_for_vehicle(session, vehicle.id))

    def test_card_number_exists_and_next_number(self) -> None:
        with self.SessionLocal() as session:
            self.assertFalse(card_number_exists(session, "000001"))
            self.assertEqual(next_card_number(session), "000001")

            _, vehicle, place = self._seed_base(session)
            session.add(
                ParkingCard(
                    card_number="000001",
                    paper_card_number=None,
                    client_id=1,
                    vehicle_id=vehicle.id,
                    place_id=place.id,
                    start_date=date(2026, 5, 21),
                    closed_at=None,
                    status="active",
                )
            )
            session.commit()

            self.assertTrue(card_number_exists(session, "000001"))
            self.assertEqual(next_card_number(session), "000002")

    def test_next_card_number_uses_max_card_number_not_row_id(self) -> None:
        with self.SessionLocal() as session:
            _, vehicle, place = self._seed_base(session)
            session.add(
                ParkingCard(
                    card_number="000010",
                    paper_card_number=None,
                    client_id=1,
                    vehicle_id=vehicle.id,
                    place_id=place.id,
                    start_date=date(2026, 5, 21),
                    closed_at=None,
                    status="active",
                )
            )
            session.commit()

            self.assertEqual(next_card_number(session), "000011")

    def test_card_refund_fields_are_persisted(self) -> None:
        with self.SessionLocal() as session:
            _, vehicle, place = self._seed_base(session)
            card = ParkingCard(
                card_number="000020",
                paper_card_number=None,
                client_id=1,
                vehicle_id=vehicle.id,
                place_id=place.id,
                start_date=date(2026, 5, 21),
                closed_at=date(2026, 5, 25),
                status="closed",
                closed_with_active_paid_period=True,
                refund_days=10,
                refund_amount_kopecks=300000,
            )
            session.add(card)
            session.commit()
            session.refresh(card)

            self.assertTrue(card.closed_with_active_paid_period)
            self.assertEqual(card.refund_days, 10)
            self.assertEqual(card.refund_amount_kopecks, 300000)

    def test_db_prevents_second_active_card_for_same_place(self) -> None:
        with self.SessionLocal() as session:
            _, vehicle, place = self._seed_base(session)
            session.add(
                ParkingCard(
                    card_number="000100",
                    paper_card_number=None,
                    client_id=1,
                    vehicle_id=vehicle.id,
                    place_id=place.id,
                    start_date=date(2026, 5, 21),
                    status="active",
                )
            )
            session.commit()

            session.add(
                ParkingCard(
                    card_number="000101",
                    paper_card_number=None,
                    client_id=1,
                    vehicle_id=vehicle.id,
                    place_id=place.id,
                    start_date=date(2026, 5, 22),
                    status="active",
                )
            )
            with self.assertRaises(IntegrityError):
                session.commit()


if __name__ == "__main__":
    unittest.main()
