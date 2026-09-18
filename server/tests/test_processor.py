from pathlib import Path

from app.processor import FFmpegProcessor
from app.schemas import Operation


def test_normalize_volume_command():
    command = FFmpegProcessor("ffmpeg").build_command(
        Operation.normalize_volume, Path("input.wav"), Path("output.mp3")
    )
    assert "-af" in command
    assert "loudnorm=I=-16:TP=-1.5:LRA=11" in command
    assert command[-1] == "output.mp3"


def test_convert_command_uses_h264_and_aac():
    command = FFmpegProcessor("ffmpeg").build_command(
        Operation.convert_mp4, Path("input.avi"), Path("output.mp4")
    )
    assert "libx264" in command
    assert "aac" in command
    assert command[-1] == "output.mp4"


def test_extract_command_disables_video():
    command = FFmpegProcessor("ffmpeg").build_command(
        Operation.extract_mp3, Path("input.mp4"), Path("output.mp3")
    )
    assert "-vn" in command
    assert "libmp3lame" in command
