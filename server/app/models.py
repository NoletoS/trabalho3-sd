from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MediaJob(Base):
    __tablename__ = "media_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    operation: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_path: Mapped[str] = mapped_column(Text, nullable=False)
    output_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_waveform_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_waveform_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_json_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    processed_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_trashed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trashed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
