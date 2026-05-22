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
    from parking_app.services.cards_table_service import (
        CardTableRow,
        build_card_table_rows,
        filter_rows_by_quick_filter,
        filter_rows_by_search,
    )


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class CardsTableServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def _create_card(self, session, *, place_number: str = "101", status: str = "active") -> ParkingCard:
        client = Client(surname="Иванов", name="Иван", patronymic="Иванович", phone="+7 (921) 111-22-33")
        session.add(client)
        session.flush()
        vehicle = Vehicle(client_id=client.id, state_number="А123АА178", brand="Lada", model="Vesta")
        session.add(vehicle)
        place = ParkingPlace(place_number=place_number, status="busy")
        session.add(place)
        session.flush()
        card = ParkingCard(
            card_number=f"C-{place_number}",
            client_id=client.id,
            vehicle_id=vehicle.id,
            place_id=place.id,
            start_date=date(2026, 1, 1),
            status=status,
        )
        session.add(card)
        session.flush()
        return card

    def test_build_card_table_rows_with_payment(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session)
            session.add(
                Payment(
                    parking_card_id=card.id,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=100,
                    status="active",
                )
            )
            session.commit()

            rows = build_card_table_rows(session, today=date(2026, 5, 21))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].paid_until, date(2026, 5, 31))
            self.assertEqual(rows[0].payment_status, "Оплачено")

    def test_build_card_table_rows_without_payments(self) -> None:
        with self.SessionLocal() as session:
            self._create_card(session)
            session.commit()

            rows = build_card_table_rows(session, today=date(2026, 5, 21))
            self.assertEqual(len(rows), 1)
            self.assertIsNone(rows[0].paid_until)
            self.assertEqual(rows[0].payment_status, "Нет оплат")

    def test_cancelled_payments_are_ignored_for_paid_until(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session)
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

            rows = build_card_table_rows(session, today=date(2026, 5, 21))
            self.assertEqual(rows[0].paid_until, date(2026, 5, 31))

    def test_filter_and_search_functions(self) -> None:
        rows = [
            CardTableRow(1, "101", "Иванов Иван", "А123АА178", "Lada Vesta", "+7 921 1112233", None, "Нет оплат", "active"),
            CardTableRow(2, "205", "Петров Пётр", "В111ВВ178", "—", "—", date(2026, 5, 10), "Просрочено", "archived"),
        ]
        self.assertEqual(len(filter_rows_by_quick_filter(rows, "Все активные")), 1)
        self.assertEqual(len(filter_rows_by_quick_filter(rows, "Архив")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "иванов")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "79211112233")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "а123аа178")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "205")), 1)


if __name__ == "__main__":
    unittest.main()
