from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .config import BACKUP_DIR, DB_PATH


def create_backup() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"aygest_{timestamp}.db"
    shutil.copy2(DB_PATH, target)
    return target


def restore_backup(source: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, DB_PATH)
