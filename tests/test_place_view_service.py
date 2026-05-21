import unittest

from parking_app.services.place_view_service import PlaceViewRow, build_place_view_row


class PlaceViewServiceTests(unittest.TestCase):
    def test_build_place_view_row(self) -> None:
        row = build_place_view_row(
            {
                "place_number": "147",
                "display_status": "occupied",
                "client_fio": "Иванов Иван Иванович",
                "state_number": "А123АА178",
                "paid_until_text": "27.09.2026",
                "payment_status": "Оплачено",
                "note": "без замечаний",
            }
        )
        self.assertIsInstance(row, PlaceViewRow)
        self.assertEqual(row.place_number, "147")
        self.assertEqual(row.display_status, "occupied")
        self.assertEqual(row.payment_status, "Оплачено")


if __name__ == "__main__":
    unittest.main()
