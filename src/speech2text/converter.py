"""Audio/video to mp3 conversion using ffmpeg."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

# Audio formats that OpenAI API accepts directly
SUPPORTED_FORMATS = {".flac", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".ogg", ".wav", ".webm"}


def _check_ffmpeg() -> str:
    """Return the path to ffmpeg, or raise RuntimeError if not found."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "ffmpeg is not installed or not found in PATH.\n"
            "Install it with: brew install ffmpeg (macOS) / apt install ffmpeg (Linux)"
        )
    return ffmpeg


def _needs_conversion(input_path: Path) -> bool:
    """Check if the file needs conversion to mp3.

    Files already in an API-supported audio format are sent directly.
    Video files or unsupported formats need conversion.
    """
    return input_path.suffix.lower() not in SUPPORTED_FORMATS


def convert_to_mp3(input_path: Path, output_path: Path | None = None) -> Path:
    """Convert an audio/video file to mp3 using ffmpeg.

    If the file is already in a supported format, return the original path.

    Args:
        input_path: Path to the input audio/video file.
        output_path: Optional explicit output path. If None, a temp file is created.

    Returns:
        Path to the mp3 file (or original if no conversion needed).

    Raises:
        FileNotFoundError: If input file does not exist.
        RuntimeError: If ffmpeg is not installed or conversion fails.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not _needs_conversion(input_path):
        return input_path

    ffmpeg = _check_ffmpeg()

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        output_path = Path(tmp.name)
        tmp.close()

    cmd = [
        ffmpeg,
        "-i", str(input_path),
        "-vn",                  # no video
        "-acodec", "libmp3lame",
        "-q:a", "2",            # high quality VBR
        "-y",                   # overwrite output
        str(output_path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,  # 5 min timeout
    )

    if result.returncode != 0:
        # Clean up failed output
        output_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"ffmpeg conversion failed (exit code {result.returncode}):\n{result.stderr}"
        )

    return output_path
