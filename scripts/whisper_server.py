"""Julia Whisper GPU Server — deploy on AutoDL RTX 3090.

Deploy:
  1. Copy to /root/autodl-tmp/julia-voice-server/
  2. pip install faster-whisper fastapi uvicorn python-multipart
  3. Set HF_HOME=/root/autodl-tmp/models
  4. python whisper_server.py --port 8001

Julia OS connects: export WHISPER_SERVER_URL="http://<autodl-ip>:8001"
"""

import argparse
import os
import tempfile
import time
from pathlib import Path

# Force cache to data disk (system disk is only 30G!)
os.environ.setdefault("HF_HOME", "/root/autodl-tmp/models")
os.environ.setdefault("TRANSFORMERS_CACHE", "/root/autodl-tmp/models")
os.environ.setdefault("XDG_CACHE_HOME", "/root/autodl-tmp/cache")

from fastapi import FastAPI, File, UploadFile
from faster_whisper import WhisperModel

app = FastAPI(title="Julia Whisper Server")

# Load model once at startup
MODEL_SIZE = os.environ.get("WHISPER_MODEL", "large-v3")
COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE", "float16")

print(f"Loading {MODEL_SIZE} ({COMPUTE_TYPE}) on CUDA...")
model = WhisperModel(MODEL_SIZE, device="cuda", compute_type=COMPUTE_TYPE)
print("Model loaded.")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": MODEL_SIZE,
        "compute": COMPUTE_TYPE,
        "device": "cuda",
    }


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Transcribe audio to text. Accepts WAV, MP3, M4A, etc."""
    t0 = time.time()

    # Save uploaded file to temp
    suffix = Path(file.filename).suffix if file.filename else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        segments, info = model.transcribe(tmp_path, language="zh", beam_size=5)
        text = " ".join(s.segment.text for s in segments).strip()
        elapsed = round(time.time() - t0, 3)

        return {
            "text": text,
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": info.duration,
            "latency": elapsed,
        }
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()

    print(f"Julia Whisper Server starting on {args.host}:{args.port}")
    print(f"  Model: {MODEL_SIZE} ({COMPUTE_TYPE})")
    print(f"  GPU: CUDA")
    print(f"  Julia OS connects via: export WHISPER_SERVER_URL='http://<ip>:{args.port}'")
    uvicorn.run(app, host=args.host, port=args.port)
