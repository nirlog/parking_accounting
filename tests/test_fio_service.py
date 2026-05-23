import unittest

from parking_app.services.fio_service import build_fio, split_fio


class FioServiceTests(unittest.TestCase):
    def test_build_fio_without_patronymic(self) -> None:
        self.assertEqual(build_fio(surname="Иванов", name="Иван"), "Иванов Иван")

    def test_build_fio_with_patronymic(self) -> None:
        self.assertEqual(
            build_fio(surname="Иванов ", name=" Иван", patronymic=" Иванович "),
            "Иванов Иван Иванович",
        )

    def test_split_fio(self) -> None:
        self.assertEqual(split_fio("Иванов Иван Иванович"), ("Иванов", "Иван", "Иванович"))
        self.assertEqual(split_fio("Иванов Иван"), ("Иванов", "Иван", None))


if __name__ == "__main__":
    unittest.main()
