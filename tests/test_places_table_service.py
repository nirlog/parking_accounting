from __future__ import annotations

from datetime import date
from importlib.util import find_spec
import unittest

SQLALCHEMY_AVAILABLE = find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from parking_app.database.db import Base
    from parking_app.database.models import Client, ParkingCard, ParkingPlace, Payment, Vehicle
    from parking_app.services.places_table_service import (
        build_place_table_rows,
        filter_place_rows,
        filter_place_rows_by_search,
    )


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class PlacesTableServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def _create_place(self, session, place_number: str, status: str = "free", note: str | None = None) -> ParkingPlace:
        place = ParkingPlace(place_number=place_number, status=status, note=note)
        session.add(place)
        session.flush()
        return place

    def _attach_active_card(
        self,
        session,
        place: ParkingPlace,
        *,
        state_number: str = "А123АА178",
        surname: str = "Иванов",
        name: str = "Иван",
        patronymic: str | None = "Иванович",
        brand: str | None = "Lada",
        model: str | None = "Vesta",
    ) -> ParkingCard:
        client = Client(surname=surname, name=name, patronymic=patronymic)
        session.add(client)
        session.flush()
        vehicle = Vehicle(client_id=client.id, state_number=state_number, brand=brand, model=model)
        session.add(vehicle)
        session.flush()
        card = ParkingCard(
            card_number=f"C-{place.place_number}-{state_number}",
            client_id=client.id,
            vehicle_id=vehicle.id,
            place_id=place.id,
            start_date=date(2026, 1, 1),
            status="active",
            vehicle_state_number=state_number,
        )
        session.add(card)
        session.flush()
        return card

    def test_free_place_without_active_card(self) -> None:
        with self.SessionLocal() as session:
            self._create_place(session, "1", status="free")
            session.commit()

            rows = build_place_table_rows(session, today=date(2026, 5, 1))
            self.assertEqual(rows[0].display_status, "free")
            self.assertEqual(rows[0].client_fio, "—")
            self.assertEqual(rows[0].payment_status, "—")

    def test_reserved_and_repair_status(self) -> None:
        with self.SessionLocal() as session:
            self._create_place(session, "2", status="reserved")
            self._create_place(session, "3", status="repair")
            session.commit()

            rows = build_place_table_rows(session, today=date(2026, 5, 1))
            statuses = {r.place_number: r.display_status for r in rows}
            self.assertEqual(statuses["2"], "reserved")
            self.assertEqual(statuses["3"], "repair")

    def test_active_card_has_priority_over_base_status(self) -> None:
        with self.SessionLocal() as session:
            place = self._create_place(session, "10", status="repair")
            self._attach_active_card(session, place)
            session.commit()

            row = build_place_table_rows(session, today=date(2026, 5, 1))[0]
            self.assertEqual(row.base_status, "repair")
            self.assertEqual(row.display_status, "occupied")

    def test_occupied_row_contains_client_vehicle_data(self) -> None:
        with self.SessionLocal() as session:
            place = self._create_place(session, "11", status="free", note="У стены")
            self._attach_active_card(session, place, state_number="А777АА178", surname="Петров", name="Пётр")
            session.commit()

            row = build_place_table_rows(session, today=date(2026, 5, 1))[0]
            self.assertEqual(row.client_fio, "Петров Пётр Иванович")
            self.assertEqual(row.state_number, "А777АА178")
            self.assertEqual(row.vehicle, "Lada Vesta")
            self.assertEqual(row.note, "У стены")

    def test_paid_until_uses_only_active_payments(self) -> None:
        with self.SessionLocal() as session:
            place = self._create_place(session, "12")
            card = self._attach_active_card(session, place)
            session.add_all(
                [
                    Payment(
                        parking_card_id=card.id,
                        payment_date=date(2026, 5, 1),
                        period_from=date(2026, 5, 1),
                        period_to=date(2026, 5, 31),
                        amount_kopecks=100,
                        status="active",
                    ),
                    Payment(
                        parking_card_id=card.id,
                        payment_date=date(2026, 6, 1),
                        period_from=date(2026, 6, 1),
                        period_to=date(2026, 6, 30),
                        amount_kopecks=100,
                        status="cancelled",
                    ),
                ]
            )
            session.commit()

            row = build_place_table_rows(session, today=date(2026, 5, 10))[0]
            self.assertEqual(row.paid_until, date(2026, 5, 31))

    def test_filters(self) -> None:
        with self.SessionLocal() as session:
            free_place = self._create_place(session, "1", status="free")
            overdue_place = self._create_place(session, "2", status="free")
            occupied_place = self._create_place(session, "3", status="free")
            self._create_place(session, "4", status="reserved")
            self._create_place(session, "5", status="repair")

            overdue_card = self._attach_active_card(session, overdue_place, state_number="А111АА178")
            occupied_card = self._attach_active_card(session, occupied_place, state_number="В222ВВ178")

            session.add(
                Payment(
                    parking_card_id=overdue_card.id,
                    payment_date=date(2026, 4, 1),
                    period_from=date(2026, 4, 1),
                    period_to=date(2026, 4, 30),
                    amount_kopecks=100,
                    status="active",
                )
            )
            session.add(
                Payment(
                    parking_card_id=occupied_card.id,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=100,
                    status="active",
                )
            )
            session.commit()

            rows = build_place_table_rows(session, today=date(2026, 5, 20))
            self.assertEqual(len(filter_place_rows(rows, "Свободные")), 1)
            self.assertEqual(len(filter_place_rows(rows, "Занятые")), 2)
            self.assertEqual(len(filter_place_rows(rows, "Просроченные")), 1)

    def test_search_and_natural_sort(self) -> None:
        with self.SessionLocal() as session:
            p10 = self._create_place(session, "10", note="У въезда")
            p2 = self._create_place(session, "2")
            p1 = self._create_place(session, "1")
            p100 = self._create_place(session, "100")
            self._attach_active_card(session, p10, state_number="А123АА178", surname="Сидоров", name="Сидор")
            self._attach_active_card(session, p2, state_number="В777ВВ178", surname="Иванов", name="Иван")
            session.commit()

            rows = build_place_table_rows(session, today=date(2026, 5, 20))
            self.assertEqual([r.place_number for r in rows], ["1", "2", "10", "100"])
            self.assertEqual(len(filter_place_rows_by_search(rows, "10")), 2)  # 10 and 100 by partial place
            self.assertEqual(len(filter_place_rows_by_search(rows, "сидоров")), 1)
            self.assertEqual(len(filter_place_rows_by_search(rows, "A123")), 1)


if __name__ == "__main__":
    unittest.main()
