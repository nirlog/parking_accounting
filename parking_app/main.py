from __future__ import annotations

from parking_app.app.config import BACKUPS_DIR, DB_PATH, EXPORTS_DIR, ensure_directories
from parking_app.database.init_db import init_db


def bootstrap() -> dict[str, str]:
    ensure_directories()
    init_db()
    return {
        "db_path": str(DB_PATH),
        "exports_dir": str(EXPORTS_DIR),
        "backups_dir": str(BACKUPS_DIR),
    }


def main() -> None:
    info = bootstrap()
    print("Parking app bootstrap completed.")
    print(f"DB: {info['db_path']}")
    print(f"Exports: {info['exports_dir']}")
    print(f"Backups: {info['backups_dir']}")


if __name__ == "__main__":
    main()
