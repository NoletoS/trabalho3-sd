from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

server_dir = str(Path(__file__).resolve().parents[1])
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    storage = tmp_path / "storage"
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        storage_root=storage,
        ffmpeg_path="ffmpeg",
        ffprobe_path="ffprobe",
        max_upload_mb=1,
    )
    application = create_app(settings)

    def fake_run(_operation, _input_path: Path, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"processed-audio-media")

    def fake_waveform(_input_path: Path, output_png_path: Path) -> bool:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRfake")
        return True

    def fake_extract_audio(_input_path: Path, output_mp3_path: Path) -> bool:
        output_mp3_path.parent.mkdir(parents=True, exist_ok=True)
        output_mp3_path.write_bytes(b"fake-audio-preview")
        return True

    application.state.processor.run = fake_run
    application.state.processor.generate_waveform = fake_waveform
    application.state.processor.extract_audio_preview = fake_extract_audio
    application.state.processor.is_available = lambda: True
    application.state.processor.is_ffprobe_available = lambda: True
    with TestClient(application) as test_client:
        yield test_client
