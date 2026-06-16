# Audio Compress & Timestamps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file Python CLI script that compresses WAV audio to Opus (OGG) and generates timestamped transcription JSON using faster-whisper.

**Architecture:** Single-file `compress.py` with subprocess call to ffmpeg and faster-whisper for transcription. Input from `input/`, output to `output/audio/` and `output/transcription/`.

**Tech Stack:** Python 3.10+, faster-whisper, ffmpeg (system)

---

### Task 1: Scaffold & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `input/.gitkeep`
- Create: `output/audio/.gitkeep`
- Create: `output/transcription/.gitkeep`

- [ ] **Step 1: Create directory structure and requirements.txt**

```bash
mkdir -p input output/audio output/transcription
touch input/.gitkeep output/audio/.gitkeep output/transcription/.gitkeep
```

```txt
# requirements.txt
faster-whisper>=1.0.0
```

- [ ] **Step 2: Commit**

```bash
git add requirements.txt input/.gitkeep output/audio/.gitkeep output/transcription/.gitkeep
git commit -m "chore: scaffold project structure"
```

---

### Task 2: CLI Argument Parsing

**Files:**
- Create: `compress.py`

- [ ] **Step 1: Add argparse with --file argument**

```python
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compress audio and generate timestamped transcription."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Input audio filename (must exist in input/ directory)",
    )
    return parser.parse_args()


def validate_input(file_arg: str) -> Path:
    input_dir = Path("input")
    input_path = input_dir / file_arg
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    return input_path


def main() -> None:
    args = parse_args()
    input_path = validate_input(args.file)
    print(f"Processing: {input_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the CLI**

```bash
python compress.py --file nonexistent.wav
# Expected: Error + exit 1

touch input/test.wav
python compress.py --file test.wav
# Expected: "Processing: input/test.wav"
rm input/test.wav
```

- [ ] **Step 3: Commit**

```bash
git add compress.py
git commit -m "feat: add CLI with --file argument"
```

---

### Task 3: Compression Module

**Files:**
- Modify: `compress.py`

- [ ] **Step 1: Add compress function using ffmpeg**

```python
import subprocess


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
```

- [ ] **Step 2: Check ffmpeg availability**

Add to `main()` or as a startup check:

```python
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
```

- [ ] **Step 3: Wire compress into main and test**

Create a test WAV file and run:

```bash
python -c "
import wave, struct, math
import numpy as np

# Generate 5 seconds of 440Hz sine wave at 16kHz
sample_rate = 16000
duration = 5
t = np.linspace(0, duration, int(sample_rate * duration), False)
audio = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

with wave.open('input/test-tones.wav', 'w') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(audio.tobytes())
print('Created input/test-tones.wav')
"
python compress.py --file test-tones.wav
# Expected: "Processing: input/test-tones.wav", compression output
ls output/audio/
# Expected: test-tones.ogg
```

- [ ] **Step 4: Commit**

```bash
git add compress.py input/test-tones.wav
git commit -m "feat: add ffmpeg audio compression to Opus"
```

---

### Task 4: Transcription Module

**Files:**
- Modify: `compress.py`

- [ ] **Step 1: Add transcribe function using faster-whisper**

```python
from faster_whisper import WhisperModel


def transcribe_audio(audio_path: Path, model_name: str = "base") -> list[dict]:
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
```

- [ ] **Step 2: Wire transcription after compression in main**

```python
def write_transcription(segments: list[dict], duration: float, input_path: Path, output_dir: Path) -> None:
    import json
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
```

Update `main()`:

```python
def main() -> None:
    args = parse_args()
    check_ffmpeg()
    input_path = validate_input(args.file)

    audio_output_dir = Path("output/audio")
    transcription_output_dir = Path("output/transcription")

    compressed = compress_audio(input_path, audio_output_dir)
    segments, duration = transcribe_audio(compressed)
    write_transcription(segments, duration, input_path, transcription_output_dir)

    print("Done.")
```

- [ ] **Step 3: Test full pipeline**

```bash
# Remove previous output to test fresh
rm -f output/audio/test-tones.ogg output/transcription/test-tones.json

python compress.py --file test-tones.wav
# Expected: compresses, transcribes, writes JSON

cat output/transcription/test-tones.json
# Expected: JSON with segments (for sine wave, may not have speech — ok)
```

- [ ] **Step 4: Add --model argument**

```python
parser.add_argument(
    "--model",
    default="base",
    help="Whisper model size: tiny, base, small, medium, large-v3 (default: base)",
)
```

```python
segments, duration = transcribe_audio(compressed, model_name=args.model)
```

- [ ] **Step 5: Commit**

```bash
git add compress.py
git commit -m "feat: add faster-whisper transcription and JSON output"
```

---

### Task 5: Add English-only model support & cleanup test file

**Files:**
- Modify: `compress.py`

- [ ] **Step 1: Add --language flag**

```python
parser.add_argument(
    "--language",
    default=None,
    help="Language code (e.g., 'en'). Auto-detected if not set.",
)
```

```python
def transcribe_audio(audio_path: Path, model_name: str = "base", language: str | None = None) -> tuple[list[dict], float]:
    ...
    segs, info = model.transcribe(str(audio_path), beam_size=5, language=language)
    ...
```

- [ ] **Step 2: Remove test audio file**

```bash
git rm input/test-tones.wav
```

- [ ] **Step 3: Commit**

```bash
git add compress.py
git commit -m "feat: add --language flag, remove test file"
```
