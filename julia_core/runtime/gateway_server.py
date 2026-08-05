"""Julia Runtime Gateway v1.1 — HTTP + WebSocket + Session Management.
Usage: python julia_core/runtime/gateway_server.py --port 8100
Routes: GET /health, GET /sessions, GET/DELETE /sessions/{id}, POST /chat, WS /ws
"""

import asyncio, json as _json, logging, re, sys, time as _time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, "/Users/admin/julia_ai_assistant")
sys.path.insert(0, "/Users/admin/julia_core")

def _clean_reply(text: str) -> str:
    """Strip tool_call blocks from LLM output before sending to client."""
    return re.sub(r'```tool_call\n.*?\n```', '', text, flags=re.DOTALL).strip()

# E3.5.2: Voice Turn Ownership — who is speaking? Julia or Tony?
from julia_core.runtime.guards.turn_manager import get_turn_manager, InputClass

logger = logging.getLogger("julia.gateway")

def main():
    import uvicorn
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
    from fastapi.middleware.cors import CORSMiddleware
    from julia_core.runtime.julia_session import get_session
    from julia_core.runtime.session_store import get_store
    from julia_core.runtime.event_trace import get_collector

    app = FastAPI(title="Julia Gateway", version="1.1")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    # Map: session_id → WebSocket. For WebRTC ASR transcripts to find the right WS.
    _session_ws: dict[str, WebSocket] = {}

    # Shared voice processing — all voice input (WS or RTC) flows through here.
    def _spawn_speech_reply(ws: WebSocket, text: str, sid: str):
        """Process transcript through JuliaSession → speech.* events via WS."""
        from julia_core.runtime.presence.state_machine import get_presence, PresenceState
        js = get_session()
        store = get_store()
        pm = get_presence()
        pm.interrupted = False

        async def _process_reply():
            speech_id = ""
            trace = None
            try:
                trace = get_collector().start(sid)
                trace.record("voice.final", {"text": text[:100]})
                loop = asyncio.get_event_loop()
                reply = _clean_reply(await loop.run_in_executor(None, js.chat, text))
                trace.record("assistant.completed", {"reply": reply[:100]})

                if pm.interrupted:
                    raise asyncio.CancelledError()

                await ws.send_text(_json.dumps(pm.transition(PresenceState.SPEAKING)))

                speech_id = f"sp-{int(_time.time()*1000)}"
                get_turn_manager().julia_started_speaking(speech_id)
                await ws.send_text(_json.dumps({"type":"speech.request",
                    "data":{"speech_id":speech_id,"text_preview":reply[:80]},
                    "timestamp":_time.strftime("%H:%M:%S")}))

                chunks = [reply[i:i+80] for i in range(0, len(reply), 80)]
                for i, chunk in enumerate(chunks[:8]):
                    if pm.interrupted:
                        raise asyncio.CancelledError()
                    await ws.send_text(_json.dumps({"type":"speech.chunk",
                        "data":{"speech_id":speech_id,"text":chunk,"sequence":i},
                        "timestamp":_time.strftime("%H:%M:%S")}))
                    get_turn_manager().julia_speech_chunk(chunk)

                await ws.send_text(_json.dumps({"type":"speech.completed",
                    "data":{"speech_id":speech_id},"timestamp":_time.strftime("%H:%M:%S")}))
                await ws.send_text(_json.dumps({"type":"assistant.completed",
                    "data":{"reply":reply,"turn":js.turn_count,"topic":js.current_topic},
                    "timestamp":_time.strftime("%H:%M:%S")}))
                store.touch(sid, topic=js.current_topic, user_msg=text, assistant_msg=reply)
                trace.record("done",{"latency_ms":trace.elapsed_ms()})
                get_collector().finish()
                get_turn_manager().julia_stopped_speaking()
                await ws.send_text(_json.dumps(pm.transition(PresenceState.IDLE)))
            except asyncio.CancelledError:
                await ws.send_text(_json.dumps({"type":"speech.cancelled",
                    "data":{"speech_id":speech_id,"reason":"interrupted"},
                    "timestamp":_time.strftime("%H:%M:%S")}))
                get_turn_manager().julia_stopped_speaking()
                await ws.send_text(_json.dumps(pm.transition(PresenceState.IDLE)))
                if trace:
                    trace.record("cancelled", {"reason": "voice.started interrupt"})
                    get_collector().finish()
            except Exception:
                get_turn_manager().julia_stopped_speaking()
                pass

        return asyncio.ensure_future(_process_reply())

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "gateway-v1.1"}

    @app.post("/rtc/offer")
    async def rtc_offer(req: Request):
        """WebRTC signaling + Server-side ASR.

        Audio → WebRTC → aiortc → AudioPipeline(VAD) → ASR → transcript
        → _spawn_speech_reply(ws) → speech.* events → Client.

        Client does echoCancellation:true on getUserMedia for AEC.
        Server does ASR + speech processing.
        """
        body = await req.json()
        sdp_offer = body.get("sdp", "")
        client_type = body.get("client_type", "electron")
        session_id = body.get("session_id", "tony-main")

        from voice_runtime.transport.webrtc.session import WebRTCSession
        from voice_runtime.pipeline.audio_pipeline import AudioPipeline
        from voice_runtime.providers.local.asr.whisper_cpu import WhisperCPUProvider

        # Audio pipeline: VAD + speech boundary detection
        pipeline = AudioPipeline(sample_rate=48000)
        # Server-side ASR: faster-whisper tiny (CPU)
        asr = WhisperCPUProvider(model_size="tiny", language="zh")

        def on_transcript(text: str, is_final: bool = False):
            if not text or not is_final:
                return
            ws = _session_ws.get(session_id)
            if ws is None:
                logger.warning(f"[RTC] no WS for session={session_id}")
                return
            logger.info(f"[Voice/RTC] {text[:60]}")
            _spawn_speech_reply(ws, text, session_id)

        rtc_session = WebRTCSession(
            client_type=client_type,
            audio_pipeline=pipeline,
            asr_provider=asr,
            on_transcript=on_transcript,
        )
        answer_sdp = await rtc_session.create_answer(sdp_offer)

        trace = get_collector().start(rtc_session.id)
        trace.record("rtc.connected", {"client": client_type, "asr": "whisper_cpu"})
        get_collector().finish()

        return {
            "status": "ok",
            "sdp": answer_sdp,
            "session_id": rtc_session.id,
            "state": rtc_session.state,
        }

    @app.get("/traces")
    async def list_traces():
        return get_collector().list_recent(10)

    @app.get("/sessions")
    async def list_sessions():
        """List sessions with >0 messages only. Auto-filter empty shells."""
        all_s = get_store().list_all()
        return [s for s in all_s if s.get("message_count", 0) > 0]

    @app.post("/sessions")
    async def create_session():
        """Create a new session. Returns session_id for use in /chat."""
        sid = f"s-{int(_time.time()*1000)}"
        meta = get_store().ensure(sid)
        return {"status": "created", "session_id": sid, "title": "", "created_at": meta.get("created_at")}

    @app.get("/sessions/{sid}")
    async def get_session_meta(sid: str):
        meta = get_store().get(sid)
        if not meta:
            return {"error": "not_found"}
        return {
            "id": meta.get("id"),
            "title": meta.get("title") or "新对话",
            "created_at": meta.get("created_at"),
            "updated_at": meta.get("updated_at"),
            "message_count": meta.get("message_count", 0),
            "topics": meta.get("topics", []),
            "messages": meta.get("messages", []),
            "summary": meta.get("summary"),
            "lifecycle": meta.get("lifecycle", "draft"),
        }

    @app.delete("/sessions/{sid}")
    async def delete_session(sid: str):
        get_store().delete(sid)
        return {"status": "deleted", "session_id": sid}

    @app.post("/chat")
    async def chat_endpoint(req: Request):
        body = await req.json()
        text, sid = body.get("text",""), body.get("session_id","default")
        js, store = get_session(), get_store()
        reply = js.chat(text)
        store.touch(sid, topic=js.current_topic, user_msg=text, assistant_msg=reply)
        meta = store.get(sid)
        if meta:
            if not meta.get("title") and js.turn_count >= 2:
                store.generate_title(sid, js)
            # Auto-summarize after 6+ messages, if no summary yet
            if not meta.get("summary") and meta.get("message_count", 0) >= 6:
                import threading
                def _summarize():
                    from julia_core.runtime.session.summarizer import SessionSummarizer
                    s = SessionSummarizer.summarize(js.provider, meta.get("messages",[]), meta)
                    if s:
                        meta["summary"] = s
                        meta["lifecycle"] = "consolidated"
                        store.save()
                threading.Thread(target=_summarize, daemon=True).start()

        reply = _clean_reply(reply)
        return {"reply": reply, "turn": js.turn_count, "session_id": sid,
                "presence": js.relationship.session_mood, "topic": js.current_topic,
                "title": meta.get("title","") if meta else "",
                "summary": meta.get("summary") if meta else None}

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await ws.accept()
        js, store = get_session(), get_store()
        sid = f"ws-{id(ws)}"
        _active_speech_task: asyncio.Task | None = None  # E3.5: track for cancellation
        try:
            while True:
                msg = _json.loads(await ws.receive_text())
                msg_type = msg.get("type", "")

                # E3 Presence State Machine — fine-grained cognitive states
                from julia_core.runtime.presence.state_machine import get_presence, PresenceState
                pm = get_presence()

                # Voice events: Client → Core
                if msg_type == "session.bind":
                    # Client registers its session_id for RTC ASR lookup
                    bound_sid = msg.get("session_id", sid)
                    _session_ws[bound_sid] = ws
                    sid = bound_sid
                    await ws.send_text(_json.dumps({"type": "session.bound", "session_id": sid}))
                    continue

                elif msg_type in ("voice.started", "client.voice.started"):
                    if pm.is_interruptible():
                        pm.interrupted = True
                        # E3.5: Cancel active speech task directly (not just flag)
                        if _active_speech_task and not _active_speech_task.done():
                            _active_speech_task.cancel()
                        await ws.send_text(_json.dumps(pm.transition(PresenceState.INTERRUPTED)))
                        await ws.send_text(_json.dumps(pm.transition(PresenceState.LISTENING)))
                    else:
                        await ws.send_text(_json.dumps(pm.transition(PresenceState.LISTENING)))

                elif msg_type in ("voice.partial", "client.voice.partial"):
                    partial = msg.get("data", {}).get("text", "")
                    await ws.send_text(_json.dumps({
                        "type": "client.voice.partial", "data": {"text": partial},
                        "timestamp": _time.strftime("%H:%M:%S"),
                    }))

                elif msg_type in ("voice.final", "client.voice.final"):
                    text = msg.get("data", {}).get("text", "") or msg.get("text", "")
                    logger.info(f"[Voice/WS] final received: text={text[:80] if text else '(empty)'}")
                    if not text:
                        continue
                    sid = msg.get("session_id") or sid
                    _session_ws[sid] = ws  # Register for RTC ASR lookup

                    # E3.5.2: Voice Turn Ownership — echo or interrupt?
                    tm = get_turn_manager()
                    classification = tm.classify(text)

                    if classification == InputClass.ECHO:
                        logger.info(f"[TurnManager] echo suppressed: {text[:60]}")
                        continue

                    if classification == InputClass.INTERRUPT:
                        logger.info(f"[TurnManager] interrupt: {text[:40]}")
                        if _active_speech_task and not _active_speech_task.done():
                            _active_speech_task.cancel()
                        await ws.send_text(_json.dumps(pm.transition(PresenceState.INTERRUPTED)))
                        await ws.send_text(_json.dumps(pm.transition(PresenceState.LISTENING)))

                    await ws.send_text(_json.dumps(pm.transition(PresenceState.RECALLING)))
                    _active_speech_task = _spawn_speech_reply(ws, text, sid)
                    continue

                elif msg_type == "user.message":
                    text, sid = msg.get("content",""), msg.get("session_id",sid)

                    # E3.5.2: Voice Turn Ownership
                    tm = get_turn_manager()
                    classification = tm.classify(text)

                    if classification == InputClass.ECHO:
                        logger.info(f"[TurnManager] echo suppressed (user.message): {text[:60]}")
                        continue

                    if classification == InputClass.INTERRUPT:
                        logger.info(f"[TurnManager] interrupt (user.message): {text[:40]}")
                        if _active_speech_task and not _active_speech_task.done():
                            _active_speech_task.cancel()
                        await ws.send_text(_json.dumps(pm.transition(PresenceState.INTERRUPTED)))
                        await ws.send_text(_json.dumps(pm.transition(PresenceState.LISTENING)))

                    reply = _clean_reply(js.chat(text))
                    store.touch(sid, topic=js.current_topic, user_msg=text, assistant_msg=reply)
                    await ws.send_text(_json.dumps({"type":"presence.changed","data":{"state":"thinking"},"timestamp":_time.strftime("%H:%M:%S")}))
                    await ws.send_text(_json.dumps({"type":"assistant.completed","data":{"reply":reply,"turn":js.turn_count,"topic":js.current_topic},"timestamp":_time.strftime("%H:%M:%S")}))
                    meta = store.get(sid)
                    if meta and not meta.get("title") and js.turn_count >= 2:
                        store.generate_title(sid, js)
        except WebSocketDisconnect:
            pass

    port = int(sys.argv[2]) if len(sys.argv)>2 and sys.argv[1]=="--port" else 8100
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    logger.info(f"Gateway v1.1 :{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
