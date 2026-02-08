"""OpenAI Speech-to-Text transcription."""

from __future__ import annotations

import os
import sys
from pathlib import Path

def transcribe(
    audio_path: Path,
    model: str = "whisper-1",
    language: str | None = None,
    response_format: str = "text",
) -> str:
    """Transcribe an audio file using the OpenAI API.

    Args:
        audio_path: Path to the audio file (must be in a supported format).
        model: OpenAI model name (default: whisper-1).
        language: ISO-639-1 language code (optional).
        response_format: Output format (text, json, srt, vtt, verbose_json).

    Returns:
        Transcribed text or structured output as a string.

    Raises:
        FileNotFoundError: If audio file does not exist.
        RuntimeError: If OPENAI_API_KEY is not set.
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "Error: OPENAI_API_KEY environment variable is not set.\n"
            "Set it with: export OPENAI_API_KEY='your-api-key'",
            file=sys.stderr,
        )
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    with open(audio_path, "rb") as audio_file:
        kwargs: dict = {
            "model": model,
            "file": audio_file,
            "response_format": response_format,
        }
        if language:
            kwargs["language"] = language

        result = client.audio.transcriptions.create(**kwargs)

    # For text format, result is a string; for json formats, convert to string
    if isinstance(result, str):
        return result
    return result.text
