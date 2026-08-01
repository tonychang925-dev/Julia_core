"""Julia Core — Generic Chat Server. Persona-agnostic, provider-independent."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from julia_core.chat.session import ChatSession
from julia_core.chat.persona import Persona

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

app = FastAPI(title="Julia Core", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    text: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "julia_core", "persona": DEMO_PERSONA.name}


@app.post("/chat")
async def chat(req: ChatRequest):
    session = ChatSession(persona=DEMO_PERSONA)
    session.add_turn(req.text, f"[{DEMO_PERSONA.name}] received: {req.text}")
    session.close()
    return {"reply": f"[{DEMO_PERSONA.name}] {req.text}", "intent": "chat"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8002, reload=True)
