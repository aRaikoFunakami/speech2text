"""Tests for the converter module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from speech2text.converter import (
    MAX_FILE_SIZE,
    SUPPORTED_FORMATS,
    _needs_conversion,
    convert_to_mp3,
    split_audio,
)


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


class TestSplitAudio:
    """Test split_audio function."""

    def test_small_file_returns_original(self, tmp_path: Path) -> None:
        """Files under MAX_FILE_SIZE should not be split."""
        small_file = tmp_path / "small.mp3"
        small_file.write_bytes(b"\x00" * 1000)
        result = split_audio(small_file)
        assert result == [small_file]

    @patch("speech2text.converter.subprocess.run")
    @patch("speech2text.converter.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_large_file_splits(self, _mock_which: object, mock_run: object, tmp_path: Path) -> None:
        """Files over MAX_FILE_SIZE should be split into chunks."""
        large_file = tmp_path / "large.mp3"
        large_file.write_bytes(b"\x00" * (MAX_FILE_SIZE + 1))

        # Mock ffprobe for duration
        ffprobe_result = MagicMock()
        ffprobe_result.returncode = 0
        ffprobe_result.stdout = '{"format": {"duration": "120.0"}}'

        # Mock ffmpeg split - create dummy chunk files
        def ffmpeg_side_effect(cmd, **kwargs):
            if "ffprobe" in str(cmd[0]):
                return ffprobe_result
            # ffmpeg segment call - create chunk files
            for arg in cmd:
                if "chunk_" in str(arg):
                    chunk_dir = Path(arg).parent
                    (chunk_dir / "chunk_000.mp3").write_bytes(b"chunk0")
                    (chunk_dir / "chunk_001.mp3").write_bytes(b"chunk1")
                    break
            result = MagicMock()
            result.returncode = 0
            return result

        mock_run.side_effect = ffmpeg_side_effect

        # Also mock ffprobe which lookup
        with patch("speech2text.converter.shutil.which", side_effect=lambda x: f"/usr/bin/{x}"):
            chunks = split_audio(large_file)

        assert len(chunks) == 2
        assert all(c.suffix == ".mp3" for c in chunks)

    @patch("speech2text.converter.subprocess.run")
    @patch("speech2text.converter.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_split_ffmpeg_failure(self, _mock_which: object, mock_run: object, tmp_path: Path) -> None:
        """Should raise RuntimeError on ffmpeg failure."""
        large_file = tmp_path / "large.mp3"
        large_file.write_bytes(b"\x00" * (MAX_FILE_SIZE + 1))

        ffprobe_result = MagicMock()
        ffprobe_result.returncode = 0
        ffprobe_result.stdout = '{"format": {"duration": "120.0"}}'

        ffmpeg_result = MagicMock()
        ffmpeg_result.returncode = 1
        ffmpeg_result.stderr = "split error"

        mock_run.side_effect = [ffprobe_result, ffmpeg_result]

        with patch("speech2text.converter.shutil.which", side_effect=lambda x: f"/usr/bin/{x}"):
            with pytest.raises(RuntimeError, match="ffmpeg split failed"):
                split_audio(large_file)
