from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3


def make_backup_filename(now: datetime | None = None) -> str:
    ts = (now or datetime.now()).strftime("%Y-%m-%d_%H%M%S")
    return f"parking_backup_{ts}.sqlite"


def backup_sqlite(db_path: Path, backups_dir: Path, now: datetime | None = None) -> Path:
    """Create a consistent SQLite backup using SQLite backup API."""
    backups_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backups_dir / make_backup_filename(now)

    source = sqlite3.connect(db_path)
    try:
        destination = sqlite3.connect(backup_path)
        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()

    return backup_path
