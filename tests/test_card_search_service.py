import unittest

from parking_app.services.card_search_service import build_search_text, filter_cards_by_query


class CardSearchServiceTests(unittest.TestCase):
    def test_build_search_text_contains_fields(self) -> None:
        text = build_search_text(
            {
                "surname": "Иванов",
                "name": "Иван",
                "phone": "79214431583",
                "state_number": "А123АА178",
                "place_number": "147",
                "card_number": "000001",
            }
        )
        self.assertIn("иванов", text)
        self.assertIn("79214431583", text)
        self.assertIn("а123аа178", text)
        self.assertIn("147", text)

    def test_filter_cards_by_query(self) -> None:
        rows = [
            {"surname": "Иванов", "state_number": "А123АА178", "place_number": "147"},
            {"surname": "Петров", "state_number": "В555ВВ178", "place_number": "201"},
        ]
        filtered = filter_cards_by_query(rows, "147")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["surname"], "Иванов")

    def test_empty_query_returns_all(self) -> None:
        rows = [{"surname": "Иванов"}, {"surname": "Петров"}]
        self.assertEqual(len(filter_cards_by_query(rows, "   ")), 2)

    def test_filter_cards_by_formatted_phone_query(self) -> None:
        rows = [
            {"surname": "Иванов", "phone": "79214431583"},
            {"surname": "Петров", "phone": "79210000000"},
        ]
        filtered = filter_cards_by_query(rows, "+7 921 443-15-83")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["surname"], "Иванов")

    def test_filter_cards_by_latin_plate_query(self) -> None:
        rows = [
            {"surname": "Иванов", "state_number": "А123АА178"},
            {"surname": "Петров", "state_number": "В555ВВ178"},
        ]
        filtered = filter_cards_by_query(rows, "A123AA178")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["surname"], "Иванов")


if __name__ == "__main__":
    unittest.main()
