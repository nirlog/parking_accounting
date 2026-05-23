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
    from parking_app.services.payments_table_service import (
        build_payment_table_rows,
        calculate_total_amount_kopecks,
        format_amount_kopecks,
    )


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class PaymentsTableServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)

    def _create_card(self, session) -> ParkingCard:
        client = Client(surname="Иванов", name="Иван", patronymic="Иванович")
        session.add(client)
        session.flush()
        vehicle = Vehicle(client_id=client.id, state_number="А123АА178")
        session.add(vehicle)
        place = ParkingPlace(place_number="101", status="free")
        session.add(place)
        session.flush()
        card = ParkingCard(
            card_number="000001",
            client_id=client.id,
            vehicle_id=vehicle.id,
            place_id=place.id,
            start_date=date(2026, 1, 1),
            status="active",
        )
        session.add(card)
        session.flush()
        return card

    def test_build_rows_contains_joined_fields(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session)
            session.add(
                Payment(
                    parking_card_id=card.id,
                    payment_date=date(2026, 5, 1),
                    period_from=date(2026, 5, 1),
                    period_to=date(2026, 5, 31),
                    amount_kopecks=800000,
                    status="active",
                )
            )
            session.commit()
            rows = build_payment_table_rows(session)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].fio, "Иванов Иван Иванович")
            self.assertEqual(rows[0].state_number, "А123АА178")
            self.assertEqual(rows[0].place_number, "101")

    def test_cancelled_hidden_by_default_and_visible_with_flag(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session)
            session.add_all(
                [
                    Payment(
                        parking_card_id=card.id,
                        payment_date=date(2026, 5, 1),
                        period_from=date(2026, 5, 1),
                        period_to=date(2026, 5, 31),
                        amount_kopecks=800000,
                        status="active",
                    ),
                    Payment(
                        parking_card_id=card.id,
                        payment_date=date(2026, 5, 2),
                        period_from=date(2026, 6, 1),
                        period_to=date(2026, 6, 30),
                        amount_kopecks=500000,
                        status="cancelled",
                    ),
                ]
            )
            session.commit()
            self.assertEqual(len(build_payment_table_rows(session)), 1)
            self.assertEqual(len(build_payment_table_rows(session, include_cancelled=True)), 2)

    def test_date_filter_works(self) -> None:
        with self.SessionLocal() as session:
            card = self._create_card(session)
            session.add_all(
                [
                    Payment(parking_card_id=card.id, payment_date=date(2026, 5, 1), period_from=date(2026, 5, 1), period_to=date(2026, 5, 31), amount_kopecks=100, status="active"),
                    Payment(parking_card_id=card.id, payment_date=date(2026, 6, 1), period_from=date(2026, 6, 1), period_to=date(2026, 6, 30), amount_kopecks=200, status="active"),
                ]
            )
            session.commit()
            rows = build_payment_table_rows(session, date_from=date(2026, 6, 1), date_to=date(2026, 6, 30))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].payment_date, date(2026, 6, 1))

    def test_total_counts_only_active(self) -> None:
        from parking_app.services.payments_table_service import PaymentTableRow

        rows = [
            PaymentTableRow(1, date(2026, 5, 1), date(2026, 5, 1), date(2026, 5, 31), 800000, "A", "B", "C", "—", "—", "—", "active", "—"),
            PaymentTableRow(2, date(2026, 5, 2), date(2026, 6, 1), date(2026, 6, 30), 500000, "A", "B", "C", "—", "—", "—", "cancelled", "—"),
        ]
        self.assertEqual(calculate_total_amount_kopecks(rows), 800000)

    def test_format_amount(self) -> None:
        self.assertEqual(format_amount_kopecks(800000), "8 000.00")
        self.assertEqual(format_amount_kopecks(800050), "8 000.50")


if __name__ == "__main__":
    unittest.main()
