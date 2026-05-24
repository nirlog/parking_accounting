from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parking_app.app.config import BACKUPS_DIR, DB_PATH, EXPORTS_DIR, ensure_directories
from parking_app.database.db import SessionLocal
from parking_app.database.init_db import init_db
from parking_app.services.settings_service import get_ui_font_settings, get_ui_theme_mode


def bootstrap() -> dict[str, str]:
    ensure_directories()
    init_db()
    return {
        "db_path": str(DB_PATH),
        "exports_dir": str(EXPORTS_DIR),
        "backups_dir": str(BACKUPS_DIR),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parking accounting application")
    parser.add_argument(
        "--bootstrap-only",
        action="store_true",
        help="Initialize storage/database and print paths without starting GUI",
    )
    return parser


def _resolve_appearance() -> tuple[str, str, int]:
    env_mode = (os.environ.get("PARKING_APP_THEME") or "").strip().lower()
    theme_mode = env_mode if env_mode in {"system", "light", "dark"} else "system"
    try:
        with SessionLocal() as session:
            if env_mode not in {"system", "light", "dark"}:
                theme_mode = get_ui_theme_mode(session)
            font = get_ui_font_settings(session)
            return theme_mode, font.family, font.size
    except Exception:
        return theme_mode, "Segoe UI", 13


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    info = bootstrap()
    print("Parking app bootstrap completed.")
    print(f"DB: {info['db_path']}")
    print(f"Exports: {info['exports_dir']}")
    print(f"Backups: {info['backups_dir']}")

    if args.bootstrap_only:
        return

    from PySide6.QtWidgets import QApplication

    from parking_app.ui.main_window import MainWindow
    from parking_app.ui.styles import apply_large_accessible_style

    app = QApplication(sys.argv)
    theme_mode, font_family, font_size = _resolve_appearance()
    apply_large_accessible_style(app, theme=theme_mode, font_family=font_family, font_size=font_size)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
