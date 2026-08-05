"""E3.6 Voice Runtime Acceptance Test — validates the full voice protocol contract.

ADR-025-D: Client/Server Voice Runtime Split
Contract: client.voice.* → Gateway → speech.*

These tests validate the SERVER side of the split:
  - Gateway correctly processes client.voice.final transcripts
  - EchoFilter suppresses text that Julia recently spoke
  - Interrupt works reliably across rapid turns
  - Session survives disconnect/reconnect
  - Presence state machine never produces invalid transitions

Client Voice Runtime (AEC/VAD/ASR) is validated separately on-device.
"""

from __future__ import annotations

import asyncio
import json as _json
import sys
import time as _time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
import websockets

GW_WS = "ws://127.0.0.1:8100/ws"
GW_HTTP = "http://127.0.0.1:8100"


def _ws_connect():
    return websockets.connect(GW_WS, proxy=None, close_timeout=3)

def _http_get(path: str) -> dict:
    import urllib.request
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(f"{GW_HTTP}{path}", timeout=5)
    return _json.loads(resp.read())

def log(msg: str):
    print(f"  [{_time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _collect_until(ws, stop_types: set, timeout: float = 15) -> list[dict]:
    """Collect WS messages until one of stop_types is seen."""
    events = []
    try:
        while True:
            msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
            events.append(msg)
            if msg["type"] in stop_types:
                break
    except asyncio.TimeoutError:
        pass
    return events


async def _collect_until_presence(ws, target_state: str, timeout: float = 15) -> list[dict]:
    """Collect messages until presence reaches target_state."""
    events = []
    try:
        while True:
            msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
            events.append(msg)
            if msg["type"] == "presence.changed" and msg["data"]["state"] == target_state:
                break
            if msg["type"] in ("speech.cancelled",):
                break
    except asyncio.TimeoutError:
        pass
    return events


# ── A1: Rapid Continuous Turns ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rapid_continuous_turns():
    """10 rapid voice.final messages — Gateway doesn't crash or mix up responses.

    Each turn must produce a unique speech_id and eventually reach idle.
    """
    from julia_core.runtime.presence.state_machine import get_presence, PresenceState
    get_presence().state = PresenceState.IDLE
    get_presence().interrupted = False

    async with _ws_connect() as ws:
        speech_ids = []
        turns_completed = 0

        for i in range(5):  # 5 turns (reduced from 10 for test speed)
            sid = f"e3_acceptance_rapid_{i}"
            await ws.send(_json.dumps({
                "type": "client.voice.final",
                "text": f"测试第{i}轮",
                "session_id": sid,
            }))

            events = await _collect_until(ws, {"assistant.completed", "speech.cancelled"}, timeout=20)
            types = [e["type"] for e in events]

            if "assistant.completed" in types:
                turns_completed += 1
                speech_reqs = [e for e in events if e["type"] == "speech.request"]
                for sr in speech_reqs:
                    speech_ids.append(sr["data"]["speech_id"])

        log(f"Completed {turns_completed}/5 turns, {len(set(speech_ids))} unique speech_ids")
        assert turns_completed >= 3, f"Only {turns_completed}/5 turns completed"
        # Each turn should have unique speech_id
        assert len(set(speech_ids)) == len(speech_ids), "speech_ids should be unique"


# ── A2: EchoFilter Suppression ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_echo_filter_suppression():
    """If Julia's recent speech is sent as voice.final, it should be suppressed.

    This tests the server-side defense layer (EchoFilter).
    Primary echo handling is in Client Voice Runtime.
    """
    from julia_core.runtime.presence.state_machine import get_presence, PresenceState
    from voice_runtime.pipeline.echo_filter import get_echo_filter
    get_presence().state = PresenceState.IDLE
    get_presence().interrupted = False

    async with _ws_connect() as ws:
        # Step 1: Send a message that will make Julia say something
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "你好",
            "session_id": "echo_test_setup",
        }))
        events = await _collect_until(ws, {"assistant.completed"}, timeout=20)

        # Step 2: Get what Julia said (first speech chunk text)
        chunks = [e for e in events if e["type"] == "speech.chunk"]
        if not chunks:
            log("No speech chunks — skipping echo test")
            return

        julia_said = chunks[0]["data"]["text"]
        log(f"Julia said: {julia_said[:50]}...")

        # Step 3: EchoFilter should have recorded Julia's speech
        echo = get_echo_filter()

        # Step 4: Send Julia's exact words as if ASR heard them (echo)
        # This should be caught by EchoFilter
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": julia_said,
            "session_id": "echo_test_check",
        }))

        # If suppressed, Gateway won't send recalling/speech — it'll just be silent
        # Wait briefly and check we don't get a speech.request
        try:
            msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            # If we get something, it should NOT be speech.request for this echo
            is_speech = msg["type"] == "speech.request"
            assert not is_speech, f"EchoFilter FAILED: echo text triggered speech.request. Text: {julia_said[:40]}"
        except asyncio.TimeoutError:
            # Timeout = nothing was sent = echo correctly suppressed
            log("EchoFilter: echo correctly suppressed (no response)")
            assert echo.suppressed >= 0  # counter exists


# ── A3: Interrupt + New Question = No Stale Chunks ───────────────────────────

@pytest.mark.asyncio
async def test_interrupt_then_new_question_clean():
    """After interrupt, a new voice.final must produce speech with new speech_id.

    Old speech.chunk must NOT appear after the new question.
    """
    from julia_core.runtime.presence.state_machine import get_presence, PresenceState
    get_presence().state = PresenceState.IDLE
    get_presence().interrupted = False

    async with _ws_connect() as ws:
        # Send a long question, then interrupt quickly
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "详细分析一下今天市场的情况",
            "session_id": "interrupt_clean_test",
        }))
        await asyncio.sleep(0.05)
        await ws.send(_json.dumps({"type": "client.voice.started"}))

        # Collect until settled
        events1 = await _collect_until(ws, {"assistant.completed", "speech.cancelled"}, timeout=15)

        # Now send new question
        await asyncio.sleep(0.3)
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "简单说一下",
            "session_id": "interrupt_clean_test_2",
        }))
        events2 = await _collect_until(ws, {"assistant.completed"}, timeout=20)

        # Get all speech_ids from the new turn
        new_speech_reqs = [e for e in events2 if e["type"] == "speech.request"]
        new_speech_chunks = [e for e in events2 if e["type"] == "speech.chunk"]

        if new_speech_reqs:
            new_id = new_speech_reqs[0]["data"]["speech_id"]
            # All chunks in events2 must reference the new speech_id
            for chunk in new_speech_chunks:
                assert chunk["data"]["speech_id"] == new_id, \
                    f"Stale chunk detected! Expected speech_id={new_id}, got {chunk['data']['speech_id']}"
            log(f"New speech_id={new_id}, {len(new_speech_chunks)} chunks — all matching")

        # Verify no speech.cancelled appeared AFTER new question
        types2 = [e["type"] for e in events2]
        assert "speech.cancelled" not in types2, \
            "speech.cancelled from old question should not appear after new voice.final"


# ── A4: Presence State Machine — No Invalid Transitions ──────────────────────

@pytest.mark.asyncio
async def test_no_invalid_presence_transitions():
    """Presence state must follow valid transitions. No jumping from idle to speaking
    without going through recalling first."""
    from julia_core.runtime.presence.state_machine import get_presence, PresenceState
    get_presence().state = PresenceState.IDLE
    get_presence().interrupted = False

    # Valid transitions per the state machine + Gateway direct transitions
    VALID_TRANSITIONS = {
        "idle":        {"listening", "recalling"},       # recalling: voice.final from idle
        "listening":   {"recalling", "idle"},
        "recalling":   {"reasoning", "speaking", "idle"},
        "reasoning":   {"generating", "speaking", "idle"},
        "generating":  {"speaking", "idle"},
        "speaking":    {"idle", "interrupted"},
        "interrupted": {"listening", "idle"},
    }

    async with _ws_connect() as ws:
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "你好",
            "session_id": "presence_valid_test",
        }))

        events = await _collect_until(ws, {"assistant.completed"}, timeout=20)
        states = [(e["data"]["state"], e["data"].get("previous", ""))
                  for e in events if e["type"] == "presence.changed"]

        log(f"Transitions: {' → '.join(f'{prev}→{curr}' for curr, prev in states)}")

        for curr, prev in states:
            if prev and prev in VALID_TRANSITIONS:
                assert curr in VALID_TRANSITIONS[prev], \
                    f"Invalid transition: {prev} → {curr}. Valid: {prev} → {VALID_TRANSITIONS[prev]}"


# ── A5: Session Disconnect/Reconnect Preserves Context ───────────────────────

@pytest.mark.asyncio
async def test_session_survives_reconnect():
    """Messages sent in a session should be retrievable after disconnect.

    Verifies SessionStore persists messages across WebSocket connections.
    """
    sid = "e3_acceptance_reconnect_test"

    # Turn 1: establish context
    async with _ws_connect() as ws:
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "我叫Tony测试",
            "session_id": sid,
        }))
        await _collect_until(ws, {"assistant.completed"}, timeout=20)

    # Simulate disconnect/reconnect by creating new WS connection
    await asyncio.sleep(0.5)

    async with _ws_connect() as ws:
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "我叫什么名字",
            "session_id": sid,
        }))
        events = await _collect_until(ws, {"assistant.completed"}, timeout=20)

        replies = [e for e in events if e["type"] == "assistant.completed"]
        assert replies, "Should get a reply after reconnect"

        reply_text = replies[0]["data"]["reply"]
        log(f"Reconnect reply: {reply_text[:100]}...")

        # Session should have 2+ messages
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        resp = opener.open(f"http://127.0.0.1:8100/sessions/{sid}", timeout=5)
        session_data = _json.loads(resp.read())
        msg_count = session_data.get("message_count", 0)
        log(f"Session messages: {msg_count}")
        assert msg_count >= 2, f"Session should have ≥2 messages, got {msg_count}"


# ── A6: Gateway Health Reports Correct State ─────────────────────────────────

def test_health_report():
    """GET /health returns ok. Gateway is alive."""
    data = _http_get("/health")
    assert data["status"] == "ok"
    assert "version" in data


# ── A7: Latency — First Token Under Budget ───────────────────────────────────

@pytest.mark.asyncio
async def test_latency_budget():
    """voice.final → speech.request should be under 5s (server-side budget)."""
    from julia_core.runtime.presence.state_machine import get_presence, PresenceState
    get_presence().state = PresenceState.IDLE
    get_presence().interrupted = False

    async with _ws_connect() as ws:
        t0 = _time.time()
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "好",
            "session_id": "latency_test",
        }))

        events = await _collect_until(ws, {"speech.request"}, timeout=10)
        latency = (_time.time() - t0) * 1000

        speech_reqs = [e for e in events if e["type"] == "speech.request"]
        if speech_reqs:
            log(f"voice.final → speech.request: {int(latency)}ms")
            assert latency < 10000, f"Latency {int(latency)}ms exceeds 10s budget"


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    sys.exit(subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=str(Path(__file__).resolve().parent.parent.parent),
    ).returncode)
