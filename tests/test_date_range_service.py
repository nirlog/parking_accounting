from datetime import date
import unittest

from parking_app.services.date_range_service import month_range, today_range, validate_custom_range


class DateRangeServiceTests(unittest.TestCase):
    def test_today_range(self) -> None:
        today = date(2026, 5, 21)
        r = today_range(today)
        self.assertEqual(r.date_from, today)
        self.assertEqual(r.date_to, today)

    def test_month_range(self) -> None:
        r = month_range(date(2026, 2, 10))
        self.assertEqual(r.date_from, date(2026, 2, 1))
        self.assertEqual(r.date_to, date(2026, 2, 28))

    def test_validate_custom_range(self) -> None:
        self.assertTrue(validate_custom_range(date(2026, 5, 1), date(2026, 5, 31)))
        self.assertFalse(validate_custom_range(date(2026, 6, 1), date(2026, 5, 31)))


if __name__ == "__main__":
    unittest.main()
