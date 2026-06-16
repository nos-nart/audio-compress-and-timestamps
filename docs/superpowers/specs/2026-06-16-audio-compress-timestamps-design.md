# Audio Compress & Timestamps — Design Spec

## Purpose

A single-file Python CLI script that compresses WAV audio to Opus (OGG) and generates word/sentence-level timestamps using faster-whisper.

## Usage

```
python compress.py --file <filename>
```

The script looks for `<filename>` inside `input/`, processes it, and writes results to `output/`.

## Directory Layout

```
.
├── input/                   # place source audio files here
├── output/
│   ├── audio/               # compressed .ogg files
│   └── transcription/       # .json transcription files
├── compress.py              # main script
└── requirements.txt
```

## Pipeline

1. **Validate** — check `input/<filename>` exists, ffmpeg is available
2. **Compress** — `ffmpeg -i input/<file> -c:a libopus -b:a 16k output/audio/<stem>.ogg`
3. **Transcribe** — faster-whisper with `base` model on the compressed OGG
4. **Write** — save JSON to `output/transcription/<stem>.json`

## Compression

| Property | Value |
|----------|-------|
| Codec    | Opus (libopus) |
| Container | OGG |
| Bitrate  | 16 kbps |
| Channels | mono (downmix if stereo) |
| Tool     | ffmpeg via subprocess |

If the input is already Opus/OGG, skip compression step.

## Transcription

- Library: `faster-whisper`
- Model: `base` (base.en for English-only)
- Language: auto-detect (or English-only if base.en used)
- Output: list of segments with `start`, `end`, `text`

## JSON Output Format

```json
{
  "file": "<original_filename>",
  "duration_sec": 123.45,
  "segments": [
    { "start": 0.0, "end": 2.5, "text": "Hello world" },
    { "start": 2.5, "end": 5.1, "text": "This is a test" }
  ]
}
```

## Dependencies

- **Python**: `faster-whisper` (≥1.0.0)
- **System**: `ffmpeg` (installed via brew/apt)

## Error Handling

- Missing input file → print error, exit 1
- ffmpeg not found → suggest install command, exit 1
- Audio too short (< 0.1s) → print warning, skip transcription
- Python import errors → print missing dependency message
- All failures exit non-zero with a clear message on stderr
