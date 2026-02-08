"""Tests for the transcriber module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from speech2text.transcriber import MAX_FILE_SIZE, transcribe


class TestTranscribe:
    """Test transcribe function."""

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            transcribe(tmp_path / "nonexistent.mp3")

    def test_file_too_large(self, tmp_path: Path) -> None:
        large_file = tmp_path / "large.mp3"
        # Create a file just over 25 MB
        large_file.write_bytes(b"\x00" * (MAX_FILE_SIZE + 1))
        with pytest.raises(ValueError, match="exceeds the 25 MB limit"):
            transcribe(large_file)

    def test_missing_api_key(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            transcribe(audio_file)

    @patch("openai.OpenAI")
    def test_successful_transcription(
        self, mock_openai_cls: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        mock_client = mock_openai_cls.return_value
        mock_client.audio.transcriptions.create.return_value = "Hello world"

        result = transcribe(audio_file)

        assert result == "Hello world"
        mock_openai_cls.assert_called_once_with(api_key="test-key")
        mock_client.audio.transcriptions.create.assert_called_once()

    @patch("openai.OpenAI")
    def test_transcription_with_language(
        self, mock_openai_cls: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        mock_client = mock_openai_cls.return_value
        mock_client.audio.transcriptions.create.return_value = "こんにちは"

        result = transcribe(audio_file, language="ja")

        assert result == "こんにちは"
        call_kwargs = mock_client.audio.transcriptions.create.call_args
        assert call_kwargs.kwargs.get("language") == "ja" or "language" in str(call_kwargs)

    @patch("openai.OpenAI")
    def test_transcription_returns_object_text(
        self, mock_openai_cls: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When response_format is json, API returns an object with .text attribute."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        mock_result = MagicMock()
        mock_result.text = "Transcribed text"
        mock_client = mock_openai_cls.return_value
        mock_client.audio.transcriptions.create.return_value = mock_result

        result = transcribe(audio_file, response_format="json")

        assert result == "Transcribed text"
