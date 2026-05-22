from datetime import date
import unittest

from parking_app.services.export_adapters_service import map_payment_row_for_export, map_payment_rows_for_export


class ExportAdaptersServiceTests(unittest.TestCase):
    def test_map_payment_row_for_export(self) -> None:
        mapped = map_payment_row_for_export(
            {
                "payment_date": date(2026, 5, 21),
                "period_from": date(2026, 5, 1),
                "period_to": date(2026, 5, 31),
                "amount_kopecks": 800000,
                "fio": "Иванов Иван",
                "state_number": "А123АА178",
                "status": "active",
            }
        )
        self.assertEqual(mapped["payment_date"], "21.05.2026")
        self.assertEqual(mapped["period_from"], "01.05.2026")
        self.assertEqual(mapped["period_to"], "31.05.2026")
        self.assertEqual(mapped["amount"], "8000.00")
        self.assertEqual(mapped["fio"], "Иванов Иван")

    def test_map_payment_rows_for_export(self) -> None:
        rows = [{"amount_kopecks": 100}, {"amount_kopecks": 200}]
        mapped = map_payment_rows_for_export(rows)
        self.assertEqual(len(mapped), 2)
        self.assertEqual(mapped[0]["amount"], "1.00")
        self.assertEqual(mapped[1]["amount"], "2.00")

    def test_map_place_from_place_number_fallback(self) -> None:
        mapped = map_payment_row_for_export({"place_number": "147"})
        self.assertEqual(mapped["place"], "147")


if __name__ == "__main__":
    unittest.main()
