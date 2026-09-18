from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


SERVER_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    database_url: str
    storage_root: Path
    ffmpeg_path: str
    ffprobe_path: str
    max_upload_mb: int = 500

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(SERVER_DIR / ".env")
        storage = Path(os.getenv("STORAGE_ROOT", "storage"))
        if not storage.is_absolute():
            storage = SERVER_DIR / storage
        return cls(
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg://postgres:postgres@localhost:5432/media_processor",
            ),
            storage_root=storage.resolve(),
            ffmpeg_path=os.getenv("FFMPEG_PATH", "ffmpeg"),
            ffprobe_path=os.getenv("FFPROBE_PATH", "ffprobe"),
            max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "500")),
        )

    @property
    def trash_dir(self) -> Path:
        return self.storage_root / "trash"

    def job_dir(self, job_id: str) -> Path:
        return self.storage_root / job_id

    def job_trash_dir(self, job_id: str) -> Path:
        return self.trash_dir / job_id
