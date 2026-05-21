from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = STORAGE_DIR / "parking.sqlite"
EXPORTS_DIR = BASE_DIR / "exports"
BACKUPS_DIR = BASE_DIR / "backups"
PHOTOS_CLIENTS_DIR = STORAGE_DIR / "photos" / "clients"
PHOTOS_VEHICLES_DIR = STORAGE_DIR / "photos" / "vehicles"


def ensure_directories() -> None:
    for folder in (STORAGE_DIR, EXPORTS_DIR, BACKUPS_DIR, PHOTOS_CLIENTS_DIR, PHOTOS_VEHICLES_DIR):
        folder.mkdir(parents=True, exist_ok=True)
