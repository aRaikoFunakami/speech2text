"""Tests for the converter module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from speech2text.converter import SUPPORTED_FORMATS, _needs_conversion, convert_to_mp3


class TestNeedsConversion:
    """Test _needs_conversion helper."""

    @pytest.mark.parametrize("ext", [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".webm", ".mp4"])
    def test_supported_formats_no_conversion(self, ext: str) -> None:
        assert _needs_conversion(Path(f"audio{ext}")) is False

    @pytest.mark.parametrize("ext", [".avi", ".mkv", ".mov", ".ts", ".wmv"])
    def test_unsupported_formats_need_conversion(self, ext: str) -> None:
        assert _needs_conversion(Path(f"video{ext}")) is True

    def test_case_insensitive(self) -> None:
        assert _needs_conversion(Path("audio.MP3")) is False
        assert _needs_conversion(Path("audio.WAV")) is False


class TestConvertToMp3:
    """Test convert_to_mp3 function."""

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            convert_to_mp3(tmp_path / "nonexistent.avi")

    def test_supported_format_returns_original(self, tmp_path: Path) -> None:
        mp3_file = tmp_path / "test.mp3"
        mp3_file.write_bytes(b"fake mp3 data")
        result = convert_to_mp3(mp3_file)
        assert result == mp3_file

    def test_wav_returns_original(self, tmp_path: Path) -> None:
        wav_file = tmp_path / "test.wav"
        wav_file.write_bytes(b"fake wav data")
        result = convert_to_mp3(wav_file)
        assert result == wav_file

    @patch("speech2text.converter.shutil.which", return_value=None)
    def test_ffmpeg_not_found(self, _mock_which: object, tmp_path: Path) -> None:
        avi_file = tmp_path / "test.avi"
        avi_file.write_bytes(b"fake avi data")
        with pytest.raises(RuntimeError, match="ffmpeg is not installed"):
            convert_to_mp3(avi_file)

    @patch("speech2text.converter.subprocess.run")
    @patch("speech2text.converter.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_ffmpeg_called_with_correct_args(
        self, _mock_which: object, mock_run: object, tmp_path: Path
    ) -> None:
        avi_file = tmp_path / "test.avi"
        avi_file.write_bytes(b"fake avi data")

        mock_run.return_value.returncode = 0  # type: ignore[attr-defined]

        result = convert_to_mp3(avi_file)

        mock_run.assert_called_once()  # type: ignore[attr-defined]
        call_args = mock_run.call_args[0][0]  # type: ignore[attr-defined]

        assert call_args[0] == "/usr/bin/ffmpeg"
        assert "-i" in call_args
        assert str(avi_file) in call_args
        assert "-vn" in call_args
        assert "-acodec" in call_args
        assert "libmp3lame" in call_args
        assert result.suffix == ".mp3"

    @patch("speech2text.converter.subprocess.run")
    @patch("speech2text.converter.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_ffmpeg_failure_raises(
        self, _mock_which: object, mock_run: object, tmp_path: Path
    ) -> None:
        avi_file = tmp_path / "test.avi"
        avi_file.write_bytes(b"fake avi data")

        mock_run.return_value.returncode = 1  # type: ignore[attr-defined]
        mock_run.return_value.stderr = "conversion error"  # type: ignore[attr-defined]

        with pytest.raises(RuntimeError, match="ffmpeg conversion failed"):
            convert_to_mp3(avi_file)
