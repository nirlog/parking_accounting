from app.config import ensure_directories
from database.init_db import init_db


def main() -> None:
    ensure_directories()
    init_db()
    print("Parking app bootstrap completed.")


if __name__ == "__main__":
    main()
