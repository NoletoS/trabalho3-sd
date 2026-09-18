from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class Operation(str, Enum):
    normalize_volume = "normalize_volume"
    convert_mp3 = "convert_mp3"
    convert_wav = "convert_wav"
    extract_mp3 = "extract_mp3"
    bass_boost = "bass_boost"
    speed_up = "speed_up"
    slow_down = "slow_down"
    convert_mp4 = "convert_mp4"
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
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    download_url: str | None = None
    original_audio_url: str | None = None
    original_waveform_url: str | None = None
    processed_audio_url: str | None = None
    processed_waveform_url: str | None = None
    meta_url: str | None = None
    original_checksum: str | None = None
    processed_checksum: str | None = None
    is_trashed: bool = False

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    database: str
    ffmpeg: str


class MetaResponse(BaseModel):
    id: str
    original_name: str
    operation: str
    status: str
    created_at: str
    completed_at: str | None = None
    original_checksum_sha256: str | None = None
    processed_checksum_sha256: str | None = None
    original_size_bytes: int | None = None
    processed_size_bytes: int | None = None
    parameters: dict[str, Any] = {}
    media_info: dict[str, Any] = {}
