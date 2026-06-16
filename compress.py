#!/usr/bin/env python3
import argparse
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


def main() -> None:
    args = parse_args()
    try:
        input_path = validate_input(args.file)
        print(f"Processing: {input_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
