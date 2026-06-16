#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compress audio and generate timestamped transcription."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Input audio filename (must exist in input/ directory)",
    )
    return parser.parse_args(args)


def validate_input(file_arg: str) -> Path:
    input_dir = Path("input")
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    input_path = input_dir / file_arg
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return input_path


def check_ffmpeg() -> None:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
    except FileNotFoundError:
        print(
            "Error: ffmpeg not found. Install it:\n"
            "  brew install ffmpeg\n"
            "  sudo apt install ffmpeg",
            file=sys.stderr,
        )
        sys.exit(1)


def compress_audio(input_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    output_path = output_dir / f"{stem}.ogg"

    if output_path.exists():
        print(f"  Compressed file exists, skipping: {output_path}")
        return output_path

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-c:a", "libopus",
        "-b:a", "16k",
        "-ac", "1",
        str(output_path),
    ]
    print(f"  Compressing: {input_path} -> {output_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: ffmpeg failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"  Done: {output_path}")
    return output_path


def main() -> None:
    args = parse_args()
    try:
        input_path = validate_input(args.file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    check_ffmpeg()

    audio_output_dir = Path("output/audio")
    compressed = compress_audio(input_path, audio_output_dir)
    print(f"Compressed: {compressed}")


if __name__ == "__main__":
    main()
