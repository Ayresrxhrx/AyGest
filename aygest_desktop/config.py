from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "AyGest Business"
APP_DIR = Path.home() / ".aygest"
APP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DIR / "aygest.db"
LOG_DIR = APP_DIR / "logs"
BACKUP_DIR = APP_DIR / "backups"
LOG_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Settings:
    api_url: str = os.getenv("AYGEST_API_URL", "")
    request_timeout: float = float(os.getenv("AYGEST_REQUEST_TIMEOUT", "15"))
    offline_grace_hours: int = int(os.getenv("AYGEST_OFFLINE_GRACE_HOURS", "72"))
    app_version: str = os.getenv("AYGEST_VERSION", "1.0.0")


settings = Settings()
