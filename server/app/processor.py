from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .schemas import Operation


OUTPUT_SUFFIXES: dict[Operation, str] = {
    Operation.normalize_volume: ".mp3",
    Operation.convert_mp3: ".mp3",
    Operation.convert_wav: ".wav",
    Operation.extract_mp3: ".mp3",
    Operation.bass_boost: ".mp3",
    Operation.speed_up: ".mp3",
    Operation.slow_down: ".mp3",
    Operation.convert_mp4: ".mp4",
    Operation.compress_video: ".mp4",
}

OPERATION_PARAMS: dict[Operation, dict[str, Any]] = {
    Operation.normalize_volume: {
        "description": "Normalização de volume (EBU R128 loudnorm)",
        "filter": "loudnorm=I=-16:TP=-1.5:LRA=11",
        "target_integrated_loudness": "-16 LUFS",
    },
    Operation.convert_mp3: {
        "description": "Conversão de áudio para formato MP3",
        "codec": "libmp3lame",
        "quality": "VBR 2 (aprox. 190 kbps)",
    },
    Operation.convert_wav: {
        "description": "Conversão de áudio para PCM WAV sem perdas",
        "codec": "pcm_s16le",
        "sample_format": "16-bit",
    },
    Operation.extract_mp3: {
        "description": "Extração de faixa de áudio em MP3",
        "codec": "libmp3lame",
        "quality": "VBR 2",
    },
    Operation.bass_boost: {
        "description": "Realce de frequências graves (Bass Boost)",
        "filter": "bass=g=8:f=110:w=0.6",
        "gain": "+8dB @ 110Hz",
    },
    Operation.speed_up: {
        "description": "Aceleração de áudio 1.25x sem alterar afinação",
        "filter": "atempo=1.25",
        "speed": "1.25x",
    },
    Operation.slow_down: {
        "description": "Desaceleração de áudio 0.85x sem alterar afinação",
        "filter": "atempo=0.85",
        "speed": "0.85x",
    },
    Operation.convert_mp4: {
        "description": "Conversão de vídeo para MP4 H.264 + AAC",
        "video_codec": "libx264 (crf 23)",
        "audio_codec": "aac 160k",
    },
    Operation.compress_video: {
        "description": "Compactação de vídeo para tamanho reduzido",
        "video_codec": "libx264 (crf 28)",
        "audio_codec": "aac 128k",
    },
}


class ProcessingError(RuntimeError):
    pass


def calculate_sha256(file_path: Path) -> str:
    """Calcula o checksum SHA-256 do arquivo em disco."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


class FFmpegProcessor:
    def __init__(self, executable: str = "ffmpeg", ffprobe_executable: str = "ffprobe") -> None:
        self.executable = executable
        self.ffprobe_executable = ffprobe_executable

    def is_available(self) -> bool:
        return bool(shutil.which(self.executable) or Path(self.executable).is_file())

    def is_ffprobe_available(self) -> bool:
        return bool(shutil.which(self.ffprobe_executable) or Path(self.ffprobe_executable).is_file())

    def get_output_suffix(self, operation: Operation, original_suffix: str) -> str:
        if operation == Operation.normalize_volume:
            lower = original_suffix.lower()
            if lower in {".wav", ".ogg", ".flac", ".m4a"}:
                return lower
            return ".mp3"
        return OUTPUT_SUFFIXES.get(operation, ".mp3")

    def build_command(
        self, operation: Operation, input_path: Path, output_path: Path
    ) -> list[str]:
        common = [
            self.executable, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(input_path),
        ]
        if operation is Operation.normalize_volume:
            return common + [
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                str(output_path),
            ]
        if operation is Operation.convert_mp3:
            return common + [
                "-vn", "-c:a", "libmp3lame", "-q:a", "2",
                str(output_path),
            ]
        if operation is Operation.convert_wav:
            return common + [
                "-vn", "-c:a", "pcm_s16le",
                str(output_path),
            ]
        if operation is Operation.extract_mp3:
            return common + [
                "-vn", "-c:a", "libmp3lame", "-q:a", "2",
                str(output_path),
            ]
        if operation is Operation.bass_boost:
            return common + [
                "-vn", "-af", "bass=g=8:f=110:w=0.6",
                str(output_path),
            ]
        if operation is Operation.speed_up:
            return common + [
                "-vn", "-filter:a", "atempo=1.25",
                str(output_path),
            ]
        if operation is Operation.slow_down:
            return common + [
                "-vn", "-filter:a", "atempo=0.85",
                str(output_path),
            ]
        if operation is Operation.convert_mp4:
            return common + [
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                str(output_path),
            ]
        if operation is Operation.compress_video:
            return common + [
                "-c:v", "libx264", "-preset", "medium", "-crf", "28",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                str(output_path),
            ]
        raise ProcessingError(f"Operação não suportada: {operation}")

    def generate_waveform(self, input_path: Path, output_png_path: Path) -> bool:
        """Gera a imagem waveform.png com a forma de onda do áudio."""
        if not self.is_available():
            return False
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        cmd = [
            self.executable, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(input_path),
            "-filter_complex", "aformat=channel_layouts=mono,showwavespic=s=800x200:colors=#36c783|#d4af37",
            "-frames:v", "1",
            str(output_png_path),
        ]
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=flags,
            )
            return output_png_path.is_file() and output_png_path.stat().st_size > 0
        except Exception:
            return False

    def get_media_info(self, file_path: Path) -> dict[str, Any]:
        """Extrai metadados de áudio/mídia via ffprobe em JSON."""
        if not self.is_ffprobe_available() or not file_path.is_file():
            return {}
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        cmd = [
            self.ffprobe_executable,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=flags,
            )
            data = json.loads(result.stdout)
            format_info = data.get("format", {})
            streams = data.get("streams", [])
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
            return {
                "duration_seconds": float(format_info.get("duration", 0.0) or 0.0),
                "bitrate_bps": int(format_info.get("bit_rate", 0) or 0),
                "format_name": format_info.get("format_name"),
                "codec_name": audio_stream.get("codec_name"),
                "sample_rate_hz": int(audio_stream.get("sample_rate", 0) or 0),
                "channels": int(audio_stream.get("channels", 0) or 0),
            }
        except Exception:
            return {}

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
