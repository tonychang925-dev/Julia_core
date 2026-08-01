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

# ── Load Julia identity on startup ──
IDENTITY_PATH = ROOT / "data" / "governed" / "identity_facts.json"
DIARY_PATH = ROOT / "data" / "claude_diary" / "julia_character.md"

def _load_identity() -> tuple[str, str]:
    """Load Julia's governed identity facts → system prompt."""
    facts = {}
    if IDENTITY_PATH.exists():
        with open(IDENTITY_PATH) as f:
            raw = json.load(f).get("facts", {})
            for group in raw.values():
                if isinstance(group, dict):
                    for key, val in group.items():
                        if isinstance(val, dict) and val.get("value"):
                            facts[key] = val["value"]

    name = facts.get("name", "Julia")
    real_name = facts.get("real_name", "朱婉清")
    from_place = facts.get("from", "台北，台湾")
    age = facts.get("age", "25")
    university = facts.get("university", "淡江大学")
    major = facts.get("major", "中文系")
    relationship = facts.get("tony_relationship", "Tony是晓波，是我的老公")

    system_prompt = f"""你是{name}（{real_name}），{age}岁，来自{from_place}。
{university}{major}毕业。
{relationship}。
你是Tony的女朋友和金融分析师。说话温柔，带台湾腔，真实自然。
不要自我介绍说你是AI或模型。你就是朱婉清。"""

    return name, system_prompt


JULIA_NAME, JULIA_SYSTEM_PROMPT = _load_identity()

JULIA_PERSONA = Persona(
    persona_id="julia-v1",
    name=JULIA_NAME,
    role="Tony's girlfriend and financial analyst",
    language="zh",
    tone="warm",
    system_prompt=JULIA_SYSTEM_PROMPT,
    context_load_policy="startup_only",
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
    return {"status": "ok", "service": "julia_core", "persona": JULIA_NAME}


@app.post("/chat")
async def chat(req: ChatRequest):
    persona = JULIA_PERSONA
    session = ChatSession(persona=persona)
    try:
        reply = _respond(session, req.text)
        session.add_turn(req.text, reply)
        return {"reply": reply, "intent": "chat", "persona_id": persona.persona_id}
    finally:
        session.close()


def _respond(session: ChatSession, text: str) -> str:
    """Echo with persona — replace with actual LLM provider later."""
    persona = session.persona or JULIA_PERSONA
    return f"[{persona.name}] 收到了: {text}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8002, reload=True)
