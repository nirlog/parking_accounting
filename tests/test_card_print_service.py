from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from parking_app.services.card_details_service import CardDetails, CardPaymentRow
from parking_app.services.card_print_service import build_card_print_html, export_card_print_html


class CardPrintServiceTests(unittest.TestCase):
    def _details(self, **overrides) -> CardDetails:
        base = CardDetails(
            card_id=1,
            card_number="000123",
            paper_card_number="147",
            card_status="active",
            start_date=date(2026, 5, 1),
            closed_at=None,
            attendant_name="Колобков",
            card_note="—",
            closed_with_active_paid_period=False,
            refund_days=0,
            refund_amount_kopecks=0,
            refund_note="—",
            client_fio="Иванов Иван Иванович",
            phone="79210000000",
            document_type="Паспорт",
            document_number="1234 567890",
            address="СПб",
            vehicle_title="Toyota Camry",
            state_number="А123АА178",
            color="Серый",
            vehicle_note="—",
            place_number="101",
            place_status="free",
            place_note="—",
            paid_until=date(2026, 5, 31),
            payment_status="Оплачено",
        )
        return CardDetails(**{**base.__dict__, **overrides})

    def _payment(self, **overrides) -> CardPaymentRow:
        base = CardPaymentRow(
            payment_id=1,
            payment_date=date(2026, 5, 1),
            period_from=date(2026, 5, 1),
            period_to=date(2026, 5, 31),
            amount_kopecks=800000,
            receipt_number="483",
            fiscal_number="ФД85",
            accepted_by="Колобков",
            status="active",
            note="ok",
        )
        return CardPaymentRow(**{**base.__dict__, **overrides})

    def test_build_card_print_html_contains_key_sections(self) -> None:
        html = build_card_print_html(self._details(), [self._payment()])
        self.assertIn("Карточка автостоянки", html)
        self.assertIn("000123", html)
        self.assertIn("Toyota Camry", html)
        self.assertIn("31.05.2026", html)
        self.assertIn("8 000.00", html)

    def test_build_card_print_html_formats_statuses(self) -> None:
        html = build_card_print_html(
            self._details(card_status="closed"),
            [self._payment(status="cancelled")],
        )
        self.assertIn("Закрыта", html)
        self.assertIn("Отменена", html)

    def test_build_card_print_html_escapes_user_content(self) -> None:
        html = build_card_print_html(
            self._details(client_fio="<script>alert(1)</script>"),
            [self._payment(note="<script>")],
        )
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)


    def test_build_card_print_html_contains_extra_details(self) -> None:
        html = build_card_print_html(
            self._details(
                attendant_name="Петров",
                card_note="Комментарий карточки",
                vehicle_note="Комментарий авто",
                place_status="repair",
                place_note="Комментарий места",
            ),
            [self._payment()],
        )
        self.assertIn("Петров", html)
        self.assertIn("Комментарий карточки", html)
        self.assertIn("Комментарий авто", html)
        self.assertIn("Ремонт", html)
        self.assertIn("Комментарий места", html)

    def test_build_card_print_html_escapes_extra_details(self) -> None:
        html = build_card_print_html(
            self._details(
                card_note="<script>",
                vehicle_note="<b>auto</b>",
                place_note="<img src=x>",
            ),
            [self._payment()],
        )
        self.assertNotIn("<script>", html)
        self.assertNotIn("<b>auto</b>", html)
        self.assertNotIn("<img src=x>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;b&gt;auto&lt;/b&gt;", html)
        self.assertIn("&lt;img src=x&gt;", html)

    def test_export_card_print_html_creates_unique_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out1 = export_card_print_html(
                output_dir=Path(tmp),
                details=self._details(),
                payments=[self._payment()],
                now=datetime(2026, 5, 1, 10, 30),
            )
            out2 = export_card_print_html(
                output_dir=Path(tmp),
                details=self._details(),
                payments=[self._payment()],
                now=datetime(2026, 5, 1, 10, 30),
            )
            self.assertTrue(out1.exists())
            self.assertTrue(out2.exists())
            self.assertNotEqual(out1, out2)


if __name__ == "__main__":
    unittest.main()
