from __future__ import annotations

import os
import platform
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_user_data_dir() -> Path:
    override = os.environ.get("PARKING_APP_DATA_DIR")
    if override:
        return Path(override).expanduser()

    if platform.system() == "Windows":
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if root:
            return Path(root) / "ParkingAccounting"
        return Path.home() / "AppData" / "Local" / "ParkingAccounting"

    data_home = os.environ.get("XDG_DATA_HOME")
    if data_home:
        return Path(data_home) / "parking_accounting"
    return Path.home() / ".local" / "share" / "parking_accounting"


APP_DATA_DIR = get_user_data_dir()
STORAGE_DIR = APP_DATA_DIR / "storage"
DB_PATH = STORAGE_DIR / "parking.sqlite"
EXPORTS_DIR = APP_DATA_DIR / "exports"
BACKUPS_DIR = APP_DATA_DIR / "backups"
PHOTOS_CLIENTS_DIR = STORAGE_DIR / "photos" / "clients"
PHOTOS_VEHICLES_DIR = STORAGE_DIR / "photos" / "vehicles"


def ensure_directories() -> None:
    for folder in (STORAGE_DIR, EXPORTS_DIR, BACKUPS_DIR, PHOTOS_CLIENTS_DIR, PHOTOS_VEHICLES_DIR):
        folder.mkdir(parents=True, exist_ok=True)
