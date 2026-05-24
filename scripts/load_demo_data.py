from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parking_app.app.config import ensure_directories
from parking_app.database.db import SessionLocal
from parking_app.database.init_db import init_db
from parking_app.services.demo_data_service import load_demo_data


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Load demo data")
    p.add_argument("--reset-demo", action="store_true", help="Reset existing demo records before load")
    p.add_argument("--data", default="demo/demo_data.json", help="Path to demo data json")
    p.add_argument("--today", default=None, help="Reference date YYYY-MM-DD")
    return p


def main() -> None:
    args = build_parser().parse_args()
    ref_today = date.fromisoformat(args.today) if args.today else None

    ensure_directories()
    init_db()

    with SessionLocal() as session:
        result = load_demo_data(
            session,
            data_path=Path(args.data),
            reset_existing_demo=args.reset_demo,
            today=ref_today,
        )
        session.commit()

    print("Demo data loaded:")
    print(f"  clients_created={result.clients_created}")
    print(f"  vehicles_created={result.vehicles_created}")
    print(f"  places_created={result.places_created}")
    print(f"  cards_created={result.cards_created}")
    print(f"  payments_created={result.payments_created}")
    print(f"  skipped_existing_cards={result.skipped_existing_cards}")


if __name__ == "__main__":
    main()
