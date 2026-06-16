#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

from faster_whisper import WhisperModel


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
    except (FileNotFoundError, OSError):
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
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        print("Error: ffmpeg timed out (300s)", file=sys.stderr)
        sys.exit(1)
    if result.returncode != 0:
        print(f"Error: ffmpeg failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"  Done: {output_path}")
    return output_path


def transcribe_audio(audio_path: Path, model_name: str = "base") -> tuple[list[dict], float]:
    print(f"  Loading whisper model: {model_name}")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")

    print(f"  Transcribing: {audio_path}")
    segments, info = model.transcribe(str(audio_path), beam_size=5)

    duration = round(info.duration, 2) if info.duration else 0
    result = []
    for seg in segments:
        result.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        })
    return result, duration


def write_transcription(segments: list[dict], duration: float, input_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    output_path = output_dir / f"{stem}.json"

    data = {
        "file": input_path.name,
        "duration_sec": duration,
        "segments": segments,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Transcription saved: {output_path}")


def main() -> None:
    args = parse_args()
    try:
        input_path = validate_input(args.file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    check_ffmpeg()

    audio_output_dir = Path("output/audio")
    transcription_output_dir = Path("output/transcription")

    compressed = compress_audio(input_path, audio_output_dir)
    segments, duration = transcribe_audio(compressed)
    write_transcription(segments, duration, input_path, transcription_output_dir)

    print("Done.")


if __name__ == "__main__":
    main()
