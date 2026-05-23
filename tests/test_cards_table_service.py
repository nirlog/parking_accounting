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

    def _create_card(
        self,
        session,
        *,
        place_number: str = "101",
        status: str = "active",
        state_number: str = "А123АА178",
    ) -> ParkingCard:
        client = Client(surname="Иванов", name="Иван", patronymic="Иванович", phone="+7 (921) 111-22-33")
        session.add(client)
        session.flush()
        vehicle = Vehicle(client_id=client.id, state_number=state_number, brand="Lada", model="Vesta")
        session.add(vehicle)
        place = ParkingPlace(place_number=place_number, status="busy")
        session.add(place)
        session.flush()
        card = ParkingCard(
            card_number=f"C-{place_number}-{state_number}",
            client_id=client.id,
            vehicle_id=vehicle.id,
            place_id=place.id,
            start_date=date(2026, 1, 1),
            status=status,
            vehicle_state_number=state_number if status == "active" else None,
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
            CardTableRow(1, "000001", "147", "101", "Иванов Иван", "А123АА178", "Lada Vesta", "+7 921 1112233", None, "Нет оплат", "active"),
            CardTableRow(2, "000002", None, "205", "Петров Пётр", "В111ВВ178", "—", "—", date(2026, 5, 10), "Просрочено", "closed"),
            CardTableRow(3, "000003", None, "306", "Сидоров Сидор", "С222СС178", "—", "—", None, "Нет оплат", "archived"),
        ]
        self.assertEqual(len(filter_rows_by_quick_filter(rows, "Все активные")), 1)
        self.assertEqual(len(filter_rows_by_quick_filter(rows, "Закрытые")), 1)
        self.assertEqual(len(filter_rows_by_quick_filter(rows, "Архив")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "иванов")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "79211112233")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "205")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "0000")), 3)
        self.assertEqual(len(filter_rows_by_search(rows, "147")), 1)

    def test_search_state_number_partial_and_normalized(self) -> None:
        rows = [CardTableRow(1, "000123", "147", "101", "Иванов Иван", "А123АА178", "Lada Vesta", "—", None, "Нет оплат", "active")]
        self.assertEqual(len(filter_rows_by_search(rows, "А123АА178")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "А123")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "A123")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "123")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "178")), 1)
        self.assertEqual(len(filter_rows_by_search(rows, "А 123-АА 178")), 1)

    def test_natural_place_sort_order(self) -> None:
        with self.SessionLocal() as session:
            self._create_card(session, place_number="10", state_number="А123АА178")
            self._create_card(session, place_number="2", state_number="В123ВВ178")
            self._create_card(session, place_number="1", state_number="С123СС178")
            self._create_card(session, place_number="100", state_number="Е123ЕЕ178")
            session.commit()

            rows = build_card_table_rows(session, today=date(2026, 5, 21))
            self.assertEqual([r.place_number for r in rows], ["1", "2", "10", "100"])

    def test_quick_filters_only_include_active_for_payment_status_filters(self) -> None:
        rows = [
            CardTableRow(1, "000001", None, "101", "A", "А111АА178", "—", "—", None, "Просрочено", "closed"),
            CardTableRow(2, "000002", None, "102", "B", "А222АА178", "—", "—", None, "Нет оплат", "archived"),
            CardTableRow(3, "000003", None, "103", "C", "А333АА178", "—", "—", None, "Просрочено", "active"),
            CardTableRow(4, "000004", None, "104", "D", "А444АА178", "—", "—", None, "Нет оплат", "active"),
            CardTableRow(5, "000005", None, "105", "E", "А555АА178", "—", "—", None, "Скоро закончится", "active"),
        ]

        overdue = filter_rows_by_quick_filter(rows, "Просроченные")
        self.assertEqual([r.card_id for r in overdue], [3])

        no_payments = filter_rows_by_quick_filter(rows, "Нет оплат")
        self.assertEqual([r.card_id for r in no_payments], [4])

        expiring = filter_rows_by_quick_filter(rows, "Оплата скоро закончится")
        self.assertEqual([r.card_id for r in expiring], [5])


if __name__ == "__main__":
    unittest.main()
