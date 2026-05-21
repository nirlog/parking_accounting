import unittest

from parking_app.services.vehicle_view_service import build_vehicle_display


class VehicleViewServiceTests(unittest.TestCase):
    def test_with_brand_and_model(self) -> None:
        self.assertEqual(
            build_vehicle_display(brand="Toyota", model="Camry", state_number="А767АВ178"),
            "Toyota Camry, А767АВ178",
        )

    def test_without_brand_model(self) -> None:
        self.assertEqual(
            build_vehicle_display(brand=None, model=None, state_number="А767АВ178"),
            "А767АВ178",
        )


if __name__ == "__main__":
    unittest.main()
