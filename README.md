# Audio Compress & Timestamps

Compress WAV audio to Opus (OGG) and generate word-level timestamped transcription JSON using faster-whisper or WhisperX. Includes a karaoke-style viewer to verify transcriptions against audio playback.

## Prerequisites

### 1. ffmpeg

```bash
brew install ffmpeg      # macOS
sudo apt install ffmpeg  # Ubuntu/Debian
```

### 2. Python dependencies

```bash
pip install faster-whisper

// OR

python3 -m pip install faster-whisper
```

### 3. Prepare input

Place your audio file(s) in the `input/` directory.

## Usage

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--file` | (required) | Input audio filename in `input/` |
| `--engine` | `faster-whisper` | Backend: `faster-whisper` or `whisperx` |
| `--model` | `base` | Model size: `tiny`, `base`, `small`, `medium`, `large-v3`, `turbo` |
| `--language` | auto | Language code (e.g. `vi`, `en`) |

### Local

```bash
# faster-whisper (default)
python3 compress.py --file audio.wav --model large-v3 --language vi

# English — turbo is fast and accurate
python3 compress.py --file audio.wav --model turbo --language en

# WhisperX — better word-level timestamp alignment
python3 compress.py --file audio.wav --engine whisperx --model large-v3
```

### Docker (both engines included)

```bash
docker build -t audio-tool .

# faster-whisper
docker run --rm \
  -e HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  audio-tool --file audio.wav --engine faster-whisper --model large-v3 --language vi

# WhisperX — better word-level timestamp alignment
docker run --rm \
  -e HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  audio-tool --file audio.wav --engine whisperx --model large-v3 --language vi

# faster-whisper + turbo (fast)
docker run --rm \
  -e HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  audio-tool --file audio.wav --engine faster-whisper --model turbo --language en
```

### Comparing engines

Run the same file with both engines and compare the resulting JSON in the viewer:

```bash
docker run ... audio-tool --file audio.wav --engine faster-whisper --model large-v3
# saves output/transcription/audio.json

# rename or move to keep both
mv output/transcription/audio.json output/transcription/audio_faster.json

docker run ... audio-tool --file audio.wav --engine whisperx --model large-v3
# saves output/transcription/audio.json
mv output/transcription/audio.json output/transcription/audio_whisperx.json
```

## Output

```
output/
├── audio/              ← compressed .ogg files
│   └── recording.ogg
└── transcription/      ← JSON with segments + word timestamps
    └── recording.json
```

### JSON format

```json
{
  "file": "recording.wav",
  "duration_sec": 123.45,
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Hello world",
      "words": [
        { "start": 0.0, "end": 0.3, "word": "Hello" },
        { "start": 0.3, "end": 0.6, "word": "world" }
      ]
    }
  ]
}
```

## Viewer (karaoke-style)

Visual verification tool that highlights words in sync with audio playback.

```
cd viewer
pnpm dev
# open http://localhost:5173
```

- **Word-level highlighting** — current word is highlighted in yellow as audio plays
- **Click to seek** — click any word to jump playback to that position
- **Auto-discovery** — dropdown lists all processed recordings from `output/`

## Pipeline

1. Validate input file exists in `input/`
2. Check ffmpeg availability
3. Compress to Opus 16 kbps mono (skips if already OGG/Opus)
4. Transcribe with selected engine (skips if audio < 0.1s)
5. Write JSON transcription with word-level timestamps

## Error handling

All failures exit non-zero with a clear message on stderr. Missing dependencies suggest the install command.
