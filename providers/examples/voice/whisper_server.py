"""Whisper STT Server — Julia's ears on GPU.

Deploy: python whisper_server.py --port 8001 --model large-v3
Client: POST /v1/transcribe with audio file → {text, language, confidence}

Architecture:
  Mic → ffmpeg capture → whisper_client.py → HTTP POST → this server
                                                         │
                                                    faster-whisper
                                                    CUDA GPU inference
                                                         │
                                                    {text, language, confidence}
"""

from __future__ import annotations

import argparse
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

# ── Config ──────────────────────────────────────────────────────────────────

MODEL_SIZE = os.environ.get("WHISPER_MODEL", "large-v3")
MODEL_PATH = os.environ.get("WHISPER_MODEL_PATH", "")  # Local model path (skip download)
MODEL_CACHE = os.environ.get("WHISPER_CACHE_DIR", "/root/autodl-tmp/models")
DEVICE = "cuda"
COMPUTE_TYPE = "float16"  # float16 for GPU, int8 for CPU

# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(title="Julia Whisper Server", version="1.0.0")

model = None
start_time = time.time()

# ── Model Loading ───────────────────────────────────────────────────────────

def load_model():
    """Load faster-whisper model. Called once at startup."""
    global model
    from faster_whisper import WhisperModel

    model_id = MODEL_PATH or MODEL_SIZE
    logging.info(f"Loading faster-whisper {model_id} on {DEVICE} ({COMPUTE_TYPE})...")
    os.makedirs(MODEL_CACHE, exist_ok=True)

    model = WhisperModel(
        model_id,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        download_root=MODEL_CACHE,
        cpu_threads=4,
        num_workers=2,
    )
    logging.info(f"Model loaded. GPU memory: {_gpu_memory()}")


def _gpu_memory() -> str:
    """Return GPU memory usage string."""
    try:
        import torch
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        return f"{allocated:.1f}G allocated, {reserved:.1f}G reserved"
    except Exception:
        return "unknown"


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model": MODEL_SIZE,
        "device": DEVICE,
        "uptime_seconds": int(time.time() - start_time),
        "gpu": _gpu_memory(),
    }


# ── Transcribe ──────────────────────────────────────────────────────────────

@app.post("/v1/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: Optional[str] = Form("zh"),
    beam_size: int = Form(5),
    vad_filter: bool = Form(True),
):
    """Transcribe audio. Returns {text, language, confidence, duration}.

    Args:
        audio: Audio file (wav, mp3, etc.)
        language: Language code. Use "zh" for auto-detect Chinese.
        beam_size: Beam size for decoding (higher = more accurate, slower).
        vad_filter: Enable voice activity detection to filter silence.
    """
    t0 = time.time()

    # Save uploaded file to temp
    suffix = Path(audio.filename).suffix if audio.filename else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        content = await audio.read()
        f.write(content)
        tmp_path = f.name

    try:
        # Transcribe
        segments, info = model.transcribe(
            tmp_path,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
            vad_parameters=dict(
                threshold=0.5,
                min_speech_duration_ms=250,
                min_silence_duration_ms=300,
            ),
        )

        # Collect results
        texts = []
        for seg in segments:
            if seg.text.strip():
                texts.append(seg.text.strip())

        full_text = "".join(texts)
        duration = time.time() - t0

        logging.info(
            f"Transcribed [{info.language} p={info.language_probability:.2f}] "
            f"in {duration:.2f}s: '{full_text[:80]}...' "
            f"({len(full_text)} chars, {len(texts)} segments)"
        )

        return {
            "text": full_text,
            "language": info.language,
            "language_probability": round(info.language_probability, 4),
            "duration": round(duration, 3),
            "segments": len(texts),
        }

    except Exception as e:
        logging.error(f"Transcription failed: {e}")
        return JSONResponse(
            {"error": str(e), "text": "", "language": "zh", "duration": 0},
            status_code=500,
        )
    finally:
        os.unlink(tmp_path)


# ── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    load_model()


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Julia Whisper STT Server")
    parser.add_argument("--port", type=int, default=8001, help="Listen port")
    parser.add_argument("--host", default="0.0.0.0", help="Listen host")
    parser.add_argument("--model", default=MODEL_SIZE, help="Whisper model size")
    args = parser.parse_args()

    MODEL_SIZE = args.model

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    logging.info(f"Starting Julia Whisper Server on {args.host}:{args.port}")
    logging.info(f"Model: {MODEL_SIZE}, Device: {DEVICE}, Cache: {MODEL_CACHE}")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
