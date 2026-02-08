"""CLI entry point for speech2text."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="speech2text",
        description="Transcribe audio/video files to text using OpenAI Speech-to-Text API",
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the audio or video file to transcribe",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="whisper-1",
        help="OpenAI model to use (default: whisper-1)",
    )
    parser.add_argument(
        "-l",
        "--language",
        default=None,
        help="Language of the input audio in ISO-639-1 format (e.g. en, ja)",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="response_format",
        default="text",
        choices=["text", "json", "srt", "vtt", "verbose_json"],
        help="Output format (default: text)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: stdout)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # Validate input file
    if not args.input_file.exists():
        print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    import shutil

    from speech2text.converter import convert_to_mp3, split_audio
    from speech2text.transcriber import transcribe

    # Convert to mp3
    mp3_path = convert_to_mp3(args.input_file)
    chunks: list[Path] = []
    tmp_dir: Path | None = None
    try:
        # Split if needed
        chunks = split_audio(mp3_path)
        if len(chunks) > 1:
            tmp_dir = chunks[0].parent
            print(
                f"Audio split into {len(chunks)} chunks for processing...",
                file=sys.stderr,
            )

        # Transcribe each chunk
        results: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            if len(chunks) > 1:
                print(
                    f"  Transcribing chunk {i}/{len(chunks)}...",
                    file=sys.stderr,
                )
            text = transcribe(
                audio_path=chunk,
                model=args.model,
                language=args.language,
                response_format=args.response_format,
            )
            results.append(text)

        result = "\n".join(results)

        # Output
        if args.output:
            args.output.write_text(result, encoding="utf-8")
        else:
            print(result)
    finally:
        # Clean up temp files
        if mp3_path != args.input_file:
            mp3_path.unlink(missing_ok=True)
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
