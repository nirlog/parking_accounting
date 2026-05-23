import unittest

from parking_app.services.place_service import match_place_filter, resolve_display_place_status


class PlaceServiceTests(unittest.TestCase):
    def test_active_card_priority(self) -> None:
        self.assertEqual(resolve_display_place_status(has_active_card=True, manual_status="repair"), "occupied")

    def test_manual_status_used_without_active_card(self) -> None:
        self.assertEqual(resolve_display_place_status(has_active_card=False, manual_status="reserved"), "reserved")

    def test_filters(self) -> None:
        self.assertTrue(match_place_filter(display_status="occupied", payment_status="Просрочено", filter_name="overdue"))
        self.assertFalse(match_place_filter(display_status="repair", payment_status="Просрочено", filter_name="overdue"))
        self.assertTrue(match_place_filter(display_status="reserved", payment_status=None, filter_name="reserved"))


if __name__ == "__main__":
    unittest.main()
