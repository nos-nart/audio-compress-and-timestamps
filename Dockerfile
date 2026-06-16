FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y ffmpeg --no-install-recommends && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir faster-whisper whisperx

WORKDIR /app
COPY compress.py .

VOLUME ["/app/input", "/app/output"]

ENTRYPOINT ["python3", "compress.py"]
