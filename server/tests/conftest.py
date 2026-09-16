from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        storage_root=tmp_path / "storage",
        ffmpeg_path="ffmpeg",
        ffprobe_path="ffprobe",
        max_upload_mb=1,
    )
    application = create_app(settings)

    def fake_run(_operation, _input_path: Path, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"processed-media")

    application.state.processor.run = fake_run
    application.state.processor.is_available = lambda: True
    with TestClient(application) as test_client:
        yield test_client
