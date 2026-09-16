from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .schemas import Operation


OUTPUT_SUFFIXES = {
    Operation.convert_mp4: ".mp4",
    Operation.extract_mp3: ".mp3",
    Operation.compress_video: ".mp4",
}


class ProcessingError(RuntimeError):
    pass


class FFmpegProcessor:
    def __init__(self, executable: str = "ffmpeg") -> None:
        self.executable = executable

    def is_available(self) -> bool:
        return bool(shutil.which(self.executable) or Path(self.executable).is_file())

    def build_command(
        self, operation: Operation, input_path: Path, output_path: Path
    ) -> list[str]:
        common = [
            self.executable, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(input_path),
        ]
        if operation is Operation.convert_mp4:
            return common + [
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                str(output_path),
            ]
        if operation is Operation.extract_mp3:
            return common + [
                "-vn", "-c:a", "libmp3lame", "-q:a", "2", str(output_path),
            ]
        if operation is Operation.compress_video:
            return common + [
                "-c:v", "libx264", "-preset", "medium", "-crf", "28",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                str(output_path),
            ]
        raise ProcessingError(f"Operação não suportada: {operation}")

    def run(self, operation: Operation, input_path: Path, output_path: Path) -> None:
        if not self.is_available():
            raise ProcessingError(
                f"FFmpeg não encontrado em '{self.executable}'. Configure FFMPEG_PATH."
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            subprocess.run(
                self.build_command(operation, input_path, output_path),
                check=True,
                capture_output=True,
                text=True,
                timeout=2 * 60 * 60,
                creationflags=flags,
            )
        except subprocess.TimeoutExpired as exc:
            output_path.unlink(missing_ok=True)
            raise ProcessingError("O processamento excedeu o limite de duas horas.") from exc
        except subprocess.CalledProcessError as exc:
            output_path.unlink(missing_ok=True)
            detail = (exc.stderr or "Falha não detalhada pelo FFmpeg").strip()
            raise ProcessingError(detail[-2000:]) from exc

        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise ProcessingError("O FFmpeg terminou sem produzir um arquivo válido.")
