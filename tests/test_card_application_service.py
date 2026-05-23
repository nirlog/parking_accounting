import unittest

from parking_app.services.card_application_service import (
    CreateCardCheckInput,
    check_create_card_allowed,
)
from parking_app.services.card_service import (
    CARD_NUMBER_ALREADY_EXISTS,
    PLACE_ALREADY_OCCUPIED,
    VEHICLE_ALREADY_ACTIVE,
)


class CardApplicationServiceTests(unittest.TestCase):
    def test_returns_place_error(self) -> None:
        result = check_create_card_allowed(
            CreateCardCheckInput(
                place_has_active_card=True,
                vehicle_has_active_card=False,
                card_number_exists=False,
            )
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, PLACE_ALREADY_OCCUPIED)

    def test_returns_vehicle_error(self) -> None:
        result = check_create_card_allowed(
            CreateCardCheckInput(
                place_has_active_card=False,
                vehicle_has_active_card=True,
                card_number_exists=False,
            )
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, VEHICLE_ALREADY_ACTIVE)

    def test_returns_card_number_error(self) -> None:
        result = check_create_card_allowed(
            CreateCardCheckInput(
                place_has_active_card=False,
                vehicle_has_active_card=False,
                card_number_exists=True,
            )
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, CARD_NUMBER_ALREADY_EXISTS)

    def test_ok(self) -> None:
        result = check_create_card_allowed(
            CreateCardCheckInput(
                place_has_active_card=False,
                vehicle_has_active_card=False,
                card_number_exists=False,
            )
        )
        self.assertTrue(result.ok)
        self.assertIsNone(result.error)


if __name__ == "__main__":
    unittest.main()
