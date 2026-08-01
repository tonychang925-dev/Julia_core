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

DEFAULT_PERSONA = Persona(
    persona_id="core-default",
    name="Assistant",
    role="helpful assistant",
    tone="friendly",
    system_prompt="You are a helpful assistant. Respond concisely in Chinese.",
)

app = FastAPI(title="Julia Core", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    text: str
    persona_id: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "service": "julia_core"}


@app.post("/chat")
async def chat(req: ChatRequest):
    session = ChatSession(persona=DEFAULT_PERSONA)
    try:
        reply = _respond(session, req.text)
        session.add_turn(req.text, reply)
        return {"reply": reply, "intent": "chat", "persona_id": session.persona.persona_id}
    finally:
        session.close()


def _respond(session: ChatSession, text: str) -> str:
    """Echo responder — replace with actual LLM provider later."""
    persona = session.persona or DEFAULT_PERSONA
    return f"[{persona.name}] 收到了你的消息: {text}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8002, reload=True)
