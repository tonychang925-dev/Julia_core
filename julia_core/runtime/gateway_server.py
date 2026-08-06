"""Julia Runtime Gateway v1.1 — HTTP + WebSocket + Session Management.
Usage: python julia_core/runtime/gateway_server.py --port 8100
Routes: GET /health, GET /sessions, GET/DELETE /sessions/{id}, POST /chat, WS /ws
"""

import asyncio, json as _json, logging, os, re, sys, time as _time
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

    # Maps for WebRTC ↔ WS binding
    _session_ws: dict[str, WebSocket] = {}       # session_id → WebSocket
    _rtc_sessions: dict[str, object] = {}         # session_id → WebRTCSession

    def _cleanup_session(sid: str):
        """E3.6: Destroy RTC session + cancel TTS producer on disconnect."""
        rtc = _rtc_sessions.pop(sid, None)
        _session_ws.pop(sid, None)
        if rtc is None:
            return
        logger.info(f"[Session] cleanup: {sid}")
        try:
            if hasattr(rtc, 'interrupt_tts'):
                rtc.interrupt_tts()
        except Exception:
            pass
        try:
            if hasattr(rtc, 'close'):
                asyncio.ensure_future(rtc.close())
        except Exception:
            pass

    # ── WS writer lock — prevents concurrent sends on same WebSocket ────
    _ws_send_locks: dict[str, asyncio.Lock] = {}

    def _get_ws_lock(sid: str) -> asyncio.Lock:
        lock = _ws_send_locks.get(sid)
        if lock is None:
            lock = asyncio.Lock()
            _ws_send_locks[sid] = lock
        return lock

    async def _send_event(ws: WebSocket, payload: dict) -> None:
        sid = payload.get("session_id", "unknown")
        async with _get_ws_lock(sid):
            await ws.send_text(_json.dumps(payload))

    def _extract_reply_text(result) -> str:
        """Extract reply string from JuliaSession return (may be str, dict, or object)."""
        if result is None:
            return ""
        if isinstance(result, str):
            return result.strip()
        if isinstance(result, dict):
            for key in ("reply", "text", "response", "content"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        for attr in ("reply", "text", "response", "content"):
            value = getattr(result, attr, None)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    # ── Ordered voice turn handler — transcript ACK → reply in ONE task ──

    def _handle_rtc_transcript(ws: WebSocket, text: str, sid: str) -> asyncio.Task:
        """Sequenced: send transcript ACK, then process through JuliaSession.

        Single task — NO concurrent ws.send_text between ACK and reply.
        """
        async def _run():
            try:
                logger.info("[Voice/RTC] handling transcript session=%s text=%r", sid, text[:80])

                # Guard: if Julia recently stopped speaking (< 3s ago), likely echo
                tm = get_turn_manager()
                if tm.seconds_since_last_speech() < 3.0:
                    logger.info("[Voice/RTC] ECHO GUARD: suppressing (%.1fs since last speech)",
                               tm.seconds_since_last_speech())
                    return

                if tm.is_speaking:
                    logger.info("[Voice/RTC] interrupting Julia for user speech")
                    rtc = _rtc_sessions.get(sid)
                    if rtc and hasattr(rtc, 'interrupt_tts'):
                        rtc.interrupt_tts()

                await _send_event(ws, {
                    "type": "client.voice.final",
                    "data": {"text": text},
                    "session_id": sid,
                    "timestamp": _time.strftime("%H:%M:%S"),
                })
                logger.info("[Voice/RTC] transcript event sent session=%s", sid)

                await _process_speech_reply(ws=ws, text=text, session_id=sid, require_tts=True)

            except asyncio.CancelledError:
                logger.info("[Voice/RTC] task cancelled session=%s", sid)
                raise
            except Exception:
                logger.exception("[Voice/RTC] turn failed session=%s text=%r", sid, text[:80])

        return asyncio.create_task(_run(), name=f"voice-turn:{sid}")

    async def _process_speech_reply(ws: WebSocket, text: str, session_id: str,
                                     require_tts: bool = False) -> None:
        """Process transcript through JuliaSession with staged logging.

        require_tts=True: caller is a voice turn from WebRTC. TTS is mandatory.
        require_tts=False: caller is text chat or WS voice.final, TTS is optional.
        """
        from julia_core.runtime.presence.state_machine import get_presence, PresenceState

        stage = "init"
        speech_id = ""
        trace = None
        js = get_session()
        store = get_store()
        pm = get_presence()
        pm.interrupted = False

        try:
            stage = "presence-recalling"
            trace = get_collector().start(session_id)
            trace.record("voice.final", {"text": text[:100]})
            await _send_event(ws, pm.transition(PresenceState.RECALLING))

            stage = "julia-process"
            logger.info("[Reply] invoking JuliaSession text=%r", text[:80])
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, js.chat, text)
            logger.info("[Reply] JuliaSession returned type=%s value=%r",
                       type(result).__name__, str(result)[:200])

            stage = "extract-reply"
            reply = _extract_reply_text(result)
            reply = _clean_reply(reply)
            if not reply:
                raise RuntimeError(f"JuliaSession returned empty reply: {result!r}")
            logger.info("[Reply] extracted reply len=%d: %r", len(reply), reply[:80])

            if pm.interrupted:
                raise asyncio.CancelledError()

            stage = "send-speech"
            await _send_event(ws, {
                **pm.transition(PresenceState.SPEAKING),
                "session_id": session_id,
            })
            speech_id = f"sp-{int(_time.time()*1000)}"
            await _send_event(ws, {
                "type": "speech.started",
                "data": {"speech_id": speech_id},
                "session_id": session_id,
                "timestamp": _time.strftime("%H:%M:%S"),
            })
            get_turn_manager().julia_started_speaking(speech_id)

            await _send_event(ws, {
                "type": "speech.request",
                "data": {"speech_id": speech_id, "text_preview": reply[:80]},
                "session_id": session_id,
                "timestamp": _time.strftime("%H:%M:%S"),
            })

            chunks = [reply[i:i+80] for i in range(0, len(reply), 80)]
            for i, chunk in enumerate(chunks[:8]):
                if pm.interrupted:
                    raise asyncio.CancelledError()
                chunk_event = {
                    "session_id": session_id,
                    "timestamp": _time.strftime("%H:%M:%S"),
                }
                await _send_event(ws, {
                    **chunk_event,
                    "type": "speech.chunk",
                    "data": {"speech_id": speech_id, "text": chunk, "sequence": i},
                })
                await _send_event(ws, {
                    **chunk_event,
                    "type": "assistant.chunk",
                    "data": {"text": chunk, "sequence": i},
                })
                get_turn_manager().julia_speech_chunk(chunk)

            stage = "tts-start"
            rtc = _rtc_sessions.get(session_id)
            if require_tts:
                if not rtc or not hasattr(rtc, 'tts_track') or not rtc.tts_track:
                    raise RuntimeError(f"Voice turn requires TTS but no RTC track for {session_id}")
                tts_gen = rtc.tts_track.begin_generation()
                from voice_runtime.providers.tts.edge_tts_pcm import EdgeTTSPCMProvider
                tts_provider = EdgeTTSPCMProvider()
                produced = await tts_provider.stream_to_track(reply, rtc.tts_track, tts_gen)
                if not produced:
                    raise RuntimeError("TTS produced no PCM frames")
                rtc.tts_track.end_generation()
                drained = await rtc.tts_track.wait_generation_consumed(tts_gen)
                if not drained:
                    raise RuntimeError("TTS drain timed out")
                logger.info("[Reply] TTS drained OK")
            elif rtc and hasattr(rtc, 'tts_track') and rtc.tts_track:
                # Non-voice turn with RTC available: best-effort TTS
                tts_gen = rtc.tts_track.begin_generation()
                from voice_runtime.providers.tts.edge_tts_pcm import EdgeTTSPCMProvider
                tts_provider = EdgeTTSPCMProvider()
                produced = await tts_provider.stream_to_track(reply, rtc.tts_track, tts_gen)
                if not produced:
                    logger.warning("[Reply] TTS produced no PCM frames (non-voice, continuing)")
                else:
                    rtc.tts_track.end_generation()
                    drained = await rtc.tts_track.wait_generation_consumed(tts_gen)
                    logger.info("[Reply] TTS drained=%s", drained)

            stage = "send-complete"
            await _send_event(ws, {
                "type": "speech.completed",
                "data": {"speech_id": speech_id},
                "session_id": session_id,
                "timestamp": _time.strftime("%H:%M:%S"),
            })
            await _send_event(ws, {
                "type": "assistant.completed",
                "data": {"reply": reply, "turn": js.turn_count, "topic": js.current_topic},
                "session_id": session_id,
                "timestamp": _time.strftime("%H:%M:%S"),
            })

            store.touch(session_id, topic=js.current_topic, user_msg=text, assistant_msg=reply)
            trace.record("done", {"latency_ms": trace.elapsed_ms()})
            get_collector().finish()
            get_turn_manager().julia_stopped_speaking()
            await _send_event(ws, pm.transition(PresenceState.IDLE))
            logger.info("[Reply] completed sid=%s reply=%r", session_id, reply[:80])

        except asyncio.CancelledError:
            logger.info("[Reply] cancelled stage=%s sid=%s", stage, session_id)
            rtc = _rtc_sessions.get(session_id)
            if rtc and hasattr(rtc, 'interrupt_tts'):
                rtc.interrupt_tts()
            await _send_event(ws, {
                "type": "speech.cancelled",
                "data": {"speech_id": speech_id, "reason": "interrupted"},
                "session_id": session_id,
                "timestamp": _time.strftime("%H:%M:%S"),
            })
            get_turn_manager().julia_stopped_speaking()
            await _send_event(ws, pm.transition(PresenceState.IDLE))
            if trace:
                trace.record("cancelled", {"reason": "voice.started interrupt"})
                get_collector().finish()
            raise

        except Exception as exc:
            logger.exception("[Reply] failed stage=%s sid=%s error=%s", stage, session_id, exc)
            get_turn_manager().julia_stopped_speaking()
            if speech_id:
                await _send_event(ws, {
                    "type": "speech.failed",
                    "data": {"speech_id": speech_id, "stage": stage, "reason": str(exc)},
                    "session_id": session_id,
                    "timestamp": _time.strftime("%H:%M:%S"),
                })
            await _send_event(ws, pm.transition(PresenceState.IDLE))

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

        # Debug: log received SDP length and ICE status
        has_ice = "ice-ufrag" in sdp_offer
        logger.info(f"[RTC] offer received: {len(sdp_offer)} bytes, ICE={has_ice}, "
                    f"sdp_preview={sdp_offer[:120]}...")

        from voice_runtime.transport.webrtc.session import WebRTCSession
        from voice_runtime.pipeline.audio_pipeline import AudioPipeline
        from voice_runtime.providers.local.asr.whisper_cpu import WhisperCPUProvider

        # Audio pipeline: VAD + speech boundary detection (PyAV resamples to 16kHz upstream)
        pipeline = AudioPipeline(sample_rate=16000)
        # Server-side ASR: faster-whisper small (or env override)
        asr = WhisperCPUProvider(
            model_size=os.environ.get("JULIA_ASR_MODEL", "small"),
            language="zh",
            compute_type=os.environ.get("JULIA_ASR_COMPUTE", "int8"),
        )

        def on_transcript(text: str, is_final: bool = False):
            if not text or not is_final:
                return
            ws = _session_ws.get(session_id)
            if ws is None:
                logger.warning(f"[RTC] no WS for session={session_id}")
                return
            logger.info(f"[Voice/RTC] transcript={text[:60]}, session={session_id}")
            _handle_rtc_transcript(ws, text, session_id)

        rtc_session = WebRTCSession(
            client_type=client_type,
            audio_pipeline=pipeline,
            asr_provider=asr,
            on_transcript=on_transcript,
        )

        try:
            answer_sdp = await rtc_session.create_answer(sdp_offer)
        except Exception as e:
            logger.error(f"[RTC] create_answer failed: {e}")
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=400, content={
                "status": "error",
                "error": f"Invalid SDP: {e}",
                "hint": "ICE ufrag/pwd required in offer SDP",
            })

        _rtc_sessions[session_id] = rtc_session

        trace = get_collector().start(rtc_session.id)
        trace.record("rtc.connected", {"client": client_type, "asr": "whisper_cpu"})
        get_collector().finish()

        return {
            "status": "ok",
            "sdp": answer_sdp,
            "type": "answer",
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
                    bound_sid = msg.get("session_id", sid)
                    _session_ws[bound_sid] = ws
                    sid = bound_sid
                    await ws.send_text(_json.dumps({"type": "session.bound", "session_id": sid}))
                    continue

                # E3.6: input.speech.started (preferred) / client.voice.started (deprecated)
                elif msg_type in ("voice.started", "client.voice.started", "input.speech.started"):
                    if pm.is_interruptible():
                        pm.interrupted = True
                        # E3.5: Cancel active speech task directly (not just flag)
                        if _active_speech_task and not _active_speech_task.done():
                            _active_speech_task.cancel()
                        # E3.6: Also interrupt TTS audio track
                        rtc = _rtc_sessions.get(sid)
                        if rtc and hasattr(rtc, 'interrupt_tts'):
                            rtc.interrupt_tts()
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

                # E3.6: input.speech.final (preferred) / client.voice.final (deprecated)
                elif msg_type in ("voice.final", "client.voice.final", "input.speech.final"):
                    text = msg.get("data", {}).get("text", "") or msg.get("text", "")
                    logger.info(f"[Voice/WS] final received: text={text[:80] if text else '(empty)'}")
                    if not text:
                        continue
                    sid = msg.get("session_id") or sid
                    _session_ws[sid] = ws  # Register for RTC ASR lookup

                    # E3.6: Julia speaking → user voice = interrupt
                    tm = get_turn_manager()
                    if tm.is_speaking:
                        logger.info("[Voice/WS] interrupting Julia for user speech")
                        if _active_speech_task and not _active_speech_task.done():
                            _active_speech_task.cancel()
                        rtc = _rtc_sessions.get(sid)
                        if rtc and hasattr(rtc, 'interrupt_tts'):
                            rtc.interrupt_tts()
                        await ws.send_text(_json.dumps(pm.transition(PresenceState.INTERRUPTED)))
                        await ws.send_text(_json.dumps(pm.transition(PresenceState.LISTENING)))

                    await ws.send_text(_json.dumps(pm.transition(PresenceState.RECALLING)))
                    _active_speech_task = asyncio.create_task(
                        _process_speech_reply(ws, text, sid), name=f"ws-turn:{sid}")
                    continue

                elif msg_type == "user.message":
                    text, sid = msg.get("content",""), msg.get("session_id",sid)

                    reply = _clean_reply(js.chat(text))
                    store.touch(sid, topic=js.current_topic, user_msg=text, assistant_msg=reply)
                    await ws.send_text(_json.dumps({"type":"presence.changed","data":{"state":"thinking"},"timestamp":_time.strftime("%H:%M:%S")}))
                    await ws.send_text(_json.dumps({"type":"assistant.completed","data":{"reply":reply,"turn":js.turn_count,"topic":js.current_topic},"timestamp":_time.strftime("%H:%M:%S")}))
                    meta = store.get(sid)
                    if meta and not meta.get("title") and js.turn_count >= 2:
                        store.generate_title(sid, js)
        except WebSocketDisconnect:
            # E3.6: Clean up RTC session on disconnect
            _cleanup_session(sid)
        finally:
            _cleanup_session(sid)

    port = int(sys.argv[2]) if len(sys.argv)>2 and sys.argv[1]=="--port" else 8100
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    logger.info(f"Gateway v1.1 :{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
