import unittest

from parking_app.services.card_service import (
    CARD_NUMBER_ALREADY_EXISTS,
    PLACE_ALREADY_OCCUPIED,
    VEHICLE_ALREADY_ACTIVE,
    validate_new_card_constraints,
)


class CardServiceTests(unittest.TestCase):
    def test_place_conflict_priority(self) -> None:
        err = validate_new_card_constraints(
            place_has_active_card=True,
            vehicle_has_active_card=True,
            card_number_exists=True,
        )
        self.assertEqual(err, PLACE_ALREADY_OCCUPIED)

    def test_vehicle_conflict(self) -> None:
        err = validate_new_card_constraints(
            place_has_active_card=False,
            vehicle_has_active_card=True,
            card_number_exists=True,
        )
        self.assertEqual(err, VEHICLE_ALREADY_ACTIVE)

    def test_card_number_conflict(self) -> None:
        err = validate_new_card_constraints(
            place_has_active_card=False,
            vehicle_has_active_card=False,
            card_number_exists=True,
        )
        self.assertEqual(err, CARD_NUMBER_ALREADY_EXISTS)

    def test_ok(self) -> None:
        err = validate_new_card_constraints(
            place_has_active_card=False,
            vehicle_has_active_card=False,
            card_number_exists=False,
        )
        self.assertIsNone(err)


if __name__ == "__main__":
    unittest.main()
