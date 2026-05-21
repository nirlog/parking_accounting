from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from parking_app.services.photo_service import copy_photo_to_storage, make_relative_storage_path


class PhotoServiceTests(unittest.TestCase):
    def test_copy_photo_to_storage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "source.jpg"
            src.write_bytes(b"img")

            dst_dir = root / "storage" / "photos" / "clients"
            dst = copy_photo_to_storage(source_path=src, target_dir=dst_dir)

            self.assertTrue(dst.exists())
            self.assertEqual(dst.read_bytes(), b"img")
            self.assertEqual(dst.name, "source.jpg")

    def test_copy_photo_to_storage_rename_if_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "source.jpg"
            src.write_bytes(b"img")

            dst_dir = root / "storage" / "photos" / "clients"
            first = copy_photo_to_storage(source_path=src, target_dir=dst_dir)
            second = copy_photo_to_storage(source_path=src, target_dir=dst_dir)

            self.assertTrue(first.exists())
            self.assertTrue(second.exists())
            self.assertNotEqual(first.name, second.name)
            self.assertEqual(second.name, "source_1.jpg")

    def test_make_relative_storage_path(self) -> None:
        base = Path("/tmp/app")
        full = base / "storage" / "photos" / "clients" / "a.jpg"
        rel = make_relative_storage_path(base_dir=base, file_path=full)
        self.assertEqual(rel, "storage/photos/clients/a.jpg")


if __name__ == "__main__":
    unittest.main()
