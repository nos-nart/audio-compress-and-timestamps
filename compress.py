#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import warnings
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
    parser.add_argument(
        "--engine",
        default="faster-whisper",
        choices=["faster-whisper", "whisperx"],
        help="Transcription backend (default: faster-whisper)",
    )
    parser.add_argument(
        "--model",
        default="base",
        help="Whisper model size or HF model ID (default: base)",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Language code (e.g., 'en'). Auto-detected if not set.",
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
    if input_path.suffix.lower() in (".ogg", ".opus"):
        print(f"  Input is already Opus/OGG, skipping compression")
        return input_path

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


def transcribe_faster_whisper(audio_path: Path, model_name: str, language: str | None) -> tuple[list[dict], float]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print(
            "Error: faster-whisper not found. Install it:\n"
            "  pip install faster-whisper",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"  Loading faster-whisper model: {model_name}")
    try:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
    except Exception as e:
        print(f"Error: failed to load whisper model '{model_name}': {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  Transcribing: {audio_path}")
    try:
        segments, info = model.transcribe(
            str(audio_path), beam_size=5, language=language,
            word_timestamps=True,
        )
    except Exception as e:
        print(f"Error: transcription failed: {e}", file=sys.stderr)
        sys.exit(1)

    duration = round(info.duration, 2) if info.duration else 0

    if duration < 0.1:
        print("  Warning: audio too short (< 0.1s), skipping transcription")
        return [], duration

    result = []
    for seg in segments:
        words = []
        if seg.words:
            for w in seg.words:
                words.append({
                    "start": round(w.start, 2),
                    "end": round(w.end, 2),
                    "word": w.word.strip(),
                })
        result.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
            "words": words,
        })
    return result, duration


def transcribe_whisperx(audio_path: Path, model_name: str, language: str | None) -> tuple[list[dict], float]:
    warnings.filterwarnings("ignore", category=UserWarning, module="pyannote")
    try:
        import whisperx
    except ImportError:
        print(
            "Error: whisperx not found. Install it:\n"
            "  pip install whisperx",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"  Loading whisperx model: {model_name}")
    device = "cpu"
    try:
        model = whisperx.load_model(model_name, device=device, compute_type="int8")
    except Exception as e:
        print(f"Error: failed to load whisperx model '{model_name}': {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  Loading audio: {audio_path}")
    try:
        audio = whisperx.load_audio(str(audio_path))
    except Exception as e:
        print(f"Error: failed to load audio: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  Transcribing: {audio_path}")
    try:
        result = model.transcribe(audio, batch_size=16, language=language)
    except Exception as e:
        print(f"Error: transcription failed: {e}", file=sys.stderr)
        sys.exit(1)

    lang = result.get("language", language or "en")
    print(f"  Aligning word timestamps (language: {lang})")
    try:
        align_model, metadata = whisperx.load_align_model(language_code=lang, device=device)
        result = whisperx.align(
            result["segments"], align_model, metadata, audio,
            device=device, return_char_alignments=False,
        )
    except Exception as e:
        print(f"  Warning: alignment failed ({e}), using raw segments")

    duration = round(max(s["end"] for s in result["segments"]), 2) if result["segments"] else 0

    if duration < 0.1:
        print("  Warning: audio too short (< 0.1s), skipping transcription")
        return [], duration

    segments_out = []
    for seg in result["segments"]:
        words = []
        for w in seg.get("words", []):
            ws = w.get("start")
            we = w.get("end")
            word = w.get("word", "").strip()
            if ws is not None and we is not None and word:
                words.append({
                    "start": round(ws, 2),
                    "end": round(we, 2),
                    "word": word,
                })
        text = seg.get("text", "").strip()
        ss = seg.get("start")
        se = seg.get("end")
        if ss is not None and se is not None:
            segments_out.append({
                "start": round(ss, 2),
                "end": round(se, 2),
                "text": text,
                "words": words,
            })
    return segments_out, duration


def write_transcription(segments: list[dict], duration: float, input_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    output_path = output_dir / f"{stem}.json"

    data = {
        "file": input_path.name,
        "duration_sec": duration,
        "segments": segments,
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (OSError, json.JSONEncodeError) as e:
        print(f"Error: failed to write transcription: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  Transcription saved: {output_path}")


BACKENDS = {
    "faster-whisper": transcribe_faster_whisper,
    "whisperx": transcribe_whisperx,
}


def main() -> None:
    args = parse_args()

    lang = args.language or "auto"
    print(f"[audio-tool] file={args.file} engine={args.engine} model={args.model} language={lang}")
    print()

    try:
        input_path = validate_input(args.file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    check_ffmpeg()

    audio_output_dir = Path("output/audio")
    transcription_output_dir = Path("output/transcription")

    compressed = compress_audio(input_path, audio_output_dir)
    transcribe = BACKENDS[args.engine]
    segments, duration = transcribe(compressed, model_name=args.model, language=args.language)
    write_transcription(segments, duration, input_path, transcription_output_dir)

    print("Done.")


if __name__ == "__main__":
    main()
