from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Operation(str, Enum):
    convert_mp4 = "convert_mp4"
    extract_mp3 = "extract_mp3"
    compress_video = "compress_video"


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobResponse(BaseModel):
    id: str
    original_name: str
    operation: Operation
    status: JobStatus
    progress: int
    file_size: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    download_url: str | None = None

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    database: str
    ffmpeg: str
