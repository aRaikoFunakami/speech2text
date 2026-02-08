"""Audio/video to mp3 conversion using ffmpeg."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

# Audio formats that OpenAI API accepts directly
SUPPORTED_FORMATS = {".flac", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".ogg", ".wav", ".webm"}

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


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


def _get_duration(audio_path: Path) -> float:
    """Get the duration of an audio file in seconds using ffprobe."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise RuntimeError("ffprobe is not found in PATH (usually installed with ffmpeg)")

    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def split_audio(audio_path: Path, max_size: int = MAX_FILE_SIZE) -> list[Path]:
    """Split an audio file into chunks that each fit under max_size.

    Uses ffmpeg segment muxer to split at roughly equal intervals.
    Each chunk is written as a separate mp3 file in a temp directory.

    Args:
        audio_path: Path to the audio file (should be mp3).
        max_size: Maximum file size per chunk in bytes.

    Returns:
        List of Paths to the chunk files, in order.
    """
    file_size = audio_path.stat().st_size
    if file_size <= max_size:
        return [audio_path]

    ffmpeg = _check_ffmpeg()
    duration = _get_duration(audio_path)

    # Estimate number of chunks needed, add margin
    num_chunks = int(file_size / max_size) + 1
    segment_duration = int(duration / num_chunks)
    # Ensure at least 10 seconds per segment
    segment_duration = max(segment_duration, 10)

    tmp_dir = Path(tempfile.mkdtemp(prefix="speech2text_split_"))
    output_pattern = str(tmp_dir / "chunk_%03d.mp3")

    cmd = [
        ffmpeg,
        "-i", str(audio_path),
        "-f", "segment",
        "-segment_time", str(segment_duration),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "2",
        "-y",
        output_pattern,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,  # 10 min timeout for large files
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg split failed (exit code {result.returncode}):\n{result.stderr}"
        )

    chunks = sorted(tmp_dir.glob("chunk_*.mp3"))
    if not chunks:
        raise RuntimeError("ffmpeg split produced no output files")

    return chunks
