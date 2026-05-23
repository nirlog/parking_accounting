from __future__ import annotations

from pathlib import Path
import shutil


def copy_photo_to_storage(*, source_path: Path, target_dir: Path) -> Path:
    """Copy selected photo file to storage directory and return new path.

    If file with the same name exists, appends numeric suffix.
    """
    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"Source photo not found: {source_path}")

    target_dir.mkdir(parents=True, exist_ok=True)

    candidate = target_dir / source_path.name
    if not candidate.exists():
        shutil.copy2(source_path, candidate)
        return candidate

    stem = source_path.stem
    suffix = source_path.suffix
    counter = 1
    while True:
        candidate = target_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            shutil.copy2(source_path, candidate)
            return candidate
        counter += 1


def make_relative_storage_path(*, base_dir: Path, file_path: Path) -> str:
    """Return relative POSIX-like path for storing in DB."""
    return file_path.relative_to(base_dir).as_posix()
