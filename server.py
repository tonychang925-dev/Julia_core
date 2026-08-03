"""Julia Core — Generic Chat Server. Persona-agnostic, provider-independent."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from julia_core.chat.persona import Persona
from julia_core.client.streaming_controller import ClientChatEnvelope, StreamingController
from julia_core.voice import VoiceService

# ── Load demo persona on startup ──
DEMO_PATH = ROOT / "data" / "examples" / "demo_persona.json"


def _load_demo_persona() -> Persona:
    if DEMO_PATH.exists():
        with open(DEMO_PATH) as f:
            raw = json.load(f)
        return Persona(
            persona_id=raw.get("persona_id", "demo-v1"),
            name=raw.get("name", "Demo Assistant"),
            role=raw.get("role", "helpful assistant"),
            language=raw.get("language", "zh"),
            tone=raw.get("tone", "friendly"),
            system_prompt=raw.get("system_prompt", ""),
        )
    return Persona(
        persona_id="default-v1",
        name="Julia Core Default",
        role="helpful assistant",
    )


DEMO_PERSONA = _load_demo_persona()
STREAMING_CONTROLLER = StreamingController()
VOICE_SERVICE = VoiceService()

app = FastAPI(title="Julia Core", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
CLIENT_DIR = ROOT / "julia_core" / "client" / "static"
if CLIENT_DIR.exists():
    app.mount("/client", StaticFiles(directory=str(CLIENT_DIR)), name="julia_client")


class ChatRequest(BaseModel):
    text: str
    session_id: str | None = None
    interaction_mode: str = "text"
    voice_output: bool = False


class VoiceSynthesisRequest(BaseModel):
    text: str


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "julia_core",
        "persona": DEMO_PERSONA.name,
        "client": "available" if CLIENT_DIR.exists() else "missing",
    }


@app.get("/")
async def client_index():
    index = CLIENT_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"service": "julia_core", "client": "missing"}




@app.get("/api/voice/profile")
async def voice_profile():
    return VOICE_SERVICE.profile_trace()


@app.post("/api/voice/synthesize")
async def voice_synthesize(req: VoiceSynthesisRequest):
    result = VOICE_SERVICE.synthesize(req.text)
    if not result.ok:
        raise HTTPException(status_code=503, detail=result.trace())
    return Response(
        content=result.audio,
        media_type=result.media_type,
        headers={
            "X-Julia-Voice-Provider": result.provider,
            "X-Julia-Voice": result.voice,
        },
    )


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    envelope = ClientChatEnvelope(
        text=req.text,
        session_id=req.session_id,
        interaction_mode=req.interaction_mode,
        voice_output=req.voice_output,
    )
    return STREAMING_CONTROLLER.complete_response(envelope)


@app.post("/api/chat/stream")
async def api_chat_stream(req: ChatRequest):
    envelope = ClientChatEnvelope(
        text=req.text,
        session_id=req.session_id,
        interaction_mode=req.interaction_mode,
        voice_output=req.voice_output,
    )
    return StreamingResponse(STREAMING_CONTROLLER.stream_sse(envelope), media_type="text/event-stream")

@app.post("/chat")
async def chat(req: ChatRequest):
    return await api_chat(req)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8002, reload=True)
