"""Tests for the CLI module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from speech2text.cli import parse_args


class TestParseArgs:
    """Test argument parsing."""

    def test_input_file_required(self) -> None:
        with pytest.raises(SystemExit):
            parse_args([])

    def test_basic_args(self) -> None:
        args = parse_args(["test.mp4"])
        assert args.input_file == Path("test.mp4")
        assert args.model == "whisper-1"
        assert args.language is None
        assert args.response_format == "text"
        assert args.output is None

    def test_all_args(self) -> None:
        args = parse_args([
            "input.wav",
            "-m", "gpt-4o-transcribe",
            "-l", "ja",
            "-f", "srt",
            "-o", "output.srt",
        ])
        assert args.input_file == Path("input.wav")
        assert args.model == "gpt-4o-transcribe"
        assert args.language == "ja"
        assert args.response_format == "srt"
        assert args.output == Path("output.srt")

    def test_invalid_format(self) -> None:
        with pytest.raises(SystemExit):
            parse_args(["test.mp4", "-f", "invalid"])


class TestMain:
    """Test main function."""

    def test_nonexistent_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        from speech2text.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(["nonexistent_file.mp4"])
        assert exc_info.value.code == 1

    @patch("speech2text.transcriber.transcribe", return_value="Hello world")
    @patch("speech2text.converter.split_audio")
    @patch("speech2text.converter.convert_to_mp3")
    def test_successful_run(
        self,
        mock_convert: object,
        mock_split: object,
        mock_transcribe: object,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from speech2text.cli import main

        input_file = tmp_path / "test.mp3"
        input_file.write_bytes(b"fake mp3 data")
        mock_convert.return_value = input_file  # type: ignore[attr-defined]
        mock_split.return_value = [input_file]  # type: ignore[attr-defined]

        main([str(input_file)])

        captured = capsys.readouterr()
        assert "Hello world" in captured.out

    @patch("speech2text.transcriber.transcribe", return_value="Output text")
    @patch("speech2text.converter.split_audio")
    @patch("speech2text.converter.convert_to_mp3")
    def test_output_to_file(
        self,
        mock_convert: object,
        mock_split: object,
        mock_transcribe: object,
        tmp_path: Path,
    ) -> None:
        from speech2text.cli import main

        input_file = tmp_path / "test.mp3"
        input_file.write_bytes(b"fake mp3 data")
        output_file = tmp_path / "output.txt"
        mock_convert.return_value = input_file  # type: ignore[attr-defined]
        mock_split.return_value = [input_file]  # type: ignore[attr-defined]

        main([str(input_file), "-o", str(output_file)])

        assert output_file.read_text() == "Output text"

    @patch("speech2text.transcriber.transcribe", side_effect=["Part 1", "Part 2"])
    @patch("speech2text.converter.split_audio")
    @patch("speech2text.converter.convert_to_mp3")
    def test_large_file_multiple_chunks(
        self,
        mock_convert: object,
        mock_split: object,
        mock_transcribe: object,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from speech2text.cli import main

        input_file = tmp_path / "test.mp3"
        input_file.write_bytes(b"fake mp3 data")
        chunk1 = tmp_path / "chunk_000.mp3"
        chunk2 = tmp_path / "chunk_001.mp3"
        chunk1.write_bytes(b"chunk0")
        chunk2.write_bytes(b"chunk1")

        mock_convert.return_value = input_file  # type: ignore[attr-defined]
        mock_split.return_value = [chunk1, chunk2]  # type: ignore[attr-defined]

        main([str(input_file)])

        captured = capsys.readouterr()
        assert "Part 1" in captured.out
        assert "Part 2" in captured.out
