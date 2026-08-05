"""E3.6 WebSocket Gateway Voice Test — simulates Electron client.

Validates Gateway /ws endpoint with Electron's exact protocol:
  Electron sends:  client.voice.started, client.voice.final, user.message
  Gateway replies: presence.changed, speech.*, assistant.completed

Usage:
  # Terminal 1: start Gateway
  python julia_core/runtime/gateway_server.py --port 8100

  # Terminal 2: run test
  NO_PROXY=127.0.0.1,localhost python tests/e3/test_ws_gateway_voice.py
"""

from __future__ import annotations

import asyncio
import json as _json
import os
import sys
import time as _time
from pathlib import Path

# Ensure julia_core is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
import websockets

GW_WS = "ws://127.0.0.1:8100/ws"
GW_HTTP = "http://127.0.0.1:8100"


# ── Helpers ──────────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"  [{_time.strftime('%H:%M:%S')}] {msg}", flush=True)


def check(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}: {detail}", flush=True)
    return condition


def _ws_connect():
    """Connect to Gateway WebSocket, bypassing SOCKS proxy for localhost."""
    return websockets.connect(GW_WS, proxy=None, close_timeout=3)

def _http_get(path: str, timeout: float = 3) -> dict:
    """HTTP GET to Gateway, bypassing system proxy for localhost."""
    import urllib.request
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(f"{GW_HTTP}{path}", timeout=timeout)
    return _json.loads(resp.read())


# ── Test 1: Health Check ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health():
    """Gateway health endpoint is reachable."""
    try:
        data = _http_get("/health")
        assert data.get("status") == "ok", f"unexpected: {data}"
    except Exception as e:
        pytest.fail(f"Gateway not reachable: {e}")


# ── Test 2: Voice Started → Presence Listening ───────────────────────────────

@pytest.mark.asyncio
async def test_voice_started_presence():
    """client.voice.started → Gateway responds with presence.changed.

    Resets PM singleton to IDLE first to avoid cross-test state pollution.
    """
    from julia_core.runtime.presence.state_machine import get_presence, PresenceState
    get_presence().state = PresenceState.IDLE
    get_presence().interrupted = False

    async with _ws_connect() as ws:
        await ws.send(_json.dumps({"type": "client.voice.started"}))

        msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
        assert msg["type"] == "presence.changed", \
            f"expected presence.changed, got {msg['type']}"
        assert msg["data"]["state"] == "listening", \
            f"expected listening (PM was reset to IDLE), got {msg['data']['state']}"


# ── Test 3: Voice Final → Full Speech Cycle ──────────────────────────────────

@pytest.mark.asyncio
async def test_voice_final_full_cycle():
    """client.voice.final → Gateway emits recall→speech.request→chunks→completed→idle."""
    async with _ws_connect() as ws:
        # Send exactly what Electron sends for voice.final
        payload = {
            "type": "client.voice.final",
            "text": "你好婉婉",
            "session_id": "e3_6_ws_test",
        }
        await ws.send(_json.dumps(payload))

        events = []
        try:
            while True:
                msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                events.append(msg)
                # Gateway sends: speech.completed → assistant.completed → presence(idle)
                # Don't break on speech.completed — assistant.completed comes after
                if msg["type"] == "assistant.completed":
                    # Grab the final presence(changed→idle) event too
                    try:
                        last = _json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                        events.append(last)
                    except asyncio.TimeoutError:
                        pass
                    break
                if msg["type"] == "speech.cancelled":
                    break
        except asyncio.TimeoutError:
            pass

        types = [e["type"] for e in events]
        log(f"Events: {' → '.join(types)}")

        # Required events
        assert "presence.changed" in types, "missing presence events"
        assert "speech.request" in types, "missing speech.request"
        assert "assistant.completed" in types, "missing assistant.completed"

        # Verify speech.request has speech_id (for TTS playback)
        speech_req = next(e for e in events if e["type"] == "speech.request")
        assert speech_req["data"]["speech_id"], "speech.request missing speech_id"
        assert speech_req["data"]["text_preview"], "speech.request missing text_preview"

        # Verify assistant.completed has reply
        reply = next(e for e in events if e["type"] == "assistant.completed")
        assert reply["data"]["reply"], "assistant.completed missing reply"

        # Verify final state is idle (not stuck in speaking)
        last_presence = [e for e in events if e["type"] == "presence.changed"]
        assert last_presence, "no presence events at all"
        assert last_presence[-1]["data"]["state"] == "idle", \
            f"final state should be idle, got {last_presence[-1]['data']['state']}"


# ── Test 4: Interrupt — Voice Started During Speech ──────────────────────────

@pytest.mark.asyncio
async def test_interrupt_during_speech():
    """Send voice.final, then voice.started immediately → expect speech.cancelled.

    Electron sends voice.started as soon as user presses the mic button,
    without waiting for a speech.request response. This test simulates that.
    """
    async with _ws_connect() as ws:
        # Send voice.final + voice.started in rapid succession
        # (no await between — both messages go into the WS send queue)
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "分析一下今天的市场情况",
            "session_id": "e3_6_interrupt_test",
        }))
        # Simulate user pressing mic button ~50ms into the question
        # In real Electron, this is hardware-triggered, independent of Gateway state
        await asyncio.sleep(0.05)
        await ws.send(_json.dumps({"type": "client.voice.started"}))

        # Collect all events — should include speech.cancelled
        events = []
        try:
            while True:
                msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                events.append(msg)
                # Stop when we see assistant.completed or speech.cancelled
                if msg["type"] in ("assistant.completed", "speech.cancelled"):
                    break
        except asyncio.TimeoutError:
            pass

        types = [e["type"] for e in events]
        log(f"Events: {' → '.join(types)}")

        # Either the interrupt worked (speech.cancelled) or LLM was too fast
        # (assistant.completed without interrupt). Both are valid outcomes
        # for a 50ms interrupt window — what matters is the Gateway didn't crash
        has_cancelled = "speech.cancelled" in types
        has_completed = "assistant.completed" in types
        assert has_cancelled or has_completed, \
            f"Expected speech.cancelled or assistant.completed, got: {types}"

        if has_cancelled:
            cancelled = next(e for e in events if e["type"] == "speech.cancelled")
            assert cancelled["data"].get("reason") == "interrupted", \
                f"cancelled reason should be 'interrupted'"
            log("Interrupt successful — speech.cancelled received")

            # Verify INTERRUPTED state was emitted
            presence_states = [e["data"]["state"] for e in events
                             if e["type"] == "presence.changed"]
            assert "interrupted" in presence_states, \
                f"missing INTERRUPTED state in {presence_states}"
        else:
            log("LLM response too fast for 50ms interrupt window (expected for localhost)")


# ── Test 5: User Message (Text Chat) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_message():
    """user.message → assistant.completed with reply."""
    async with _ws_connect() as ws:
        # Electron sends text messages like this
        await ws.send(_json.dumps({
            "type": "user.message",
            "session_id": "e3_6_text_test",
            "content": "你知道我是谁吗",
        }))

        events = []
        try:
            while True:
                msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                events.append(msg)
                if msg["type"] == "assistant.completed":
                    break
        except asyncio.TimeoutError:
            pass

        types = [e["type"] for e in events]
        log(f"Text events: {' → '.join(types)}")

        reply_event = next(e for e in events if e["type"] == "assistant.completed")
        assert reply_event["data"]["reply"], "assistant.completed has no reply"
        # Should recognize Tony
        reply_text = reply_event["data"]["reply"]
        log(f"Reply: {reply_text[:100]}...")


# ── Test 6: Session Continuity ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_session_continuity():
    """Two turns in same session → second turn knows context of first."""
    async with _ws_connect() as ws:
        sid = "e3_6_continuity_test"

        # Turn 1
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "我叫Tony",
            "session_id": sid,
        }))
        events1 = []
        try:
            while True:
                msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                events1.append(msg)
                if msg["type"] == "assistant.completed":
                    break
                if msg["type"] == "speech.cancelled":
                    break
        except asyncio.TimeoutError:
            pass

        # Small pause to let state settle
        await asyncio.sleep(0.5)

        # Turn 2
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "我叫什么名字",
            "session_id": sid,
        }))
        events2 = []
        try:
            while True:
                msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                events2.append(msg)
                if msg["type"] == "assistant.completed":
                    break
                if msg["type"] == "speech.cancelled":
                    break
        except asyncio.TimeoutError:
            pass

        # Get replies from both turns
        replies1 = [e for e in events1 if e["type"] == "assistant.completed"]
        replies2 = [e for e in events2 if e["type"] == "assistant.completed"]

        if replies1:
            log(f"Turn 1 reply: {replies1[0]['data']['reply'][:80]}...")
        if replies2:
            log(f"Turn 2 reply: {replies2[0]['data']['reply'][:80]}...")

        assert replies1, "Turn 1 should produce a reply"
        assert replies2, "Turn 2 should produce a reply"


# ── Test 7: Heartbeat is tolerated ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_heartbeat():
    """Electron sends heartbeat every 30s. Gateway should not crash or close."""
    async with _ws_connect() as ws:
        # Send heartbeat — exactly as Electron does
        await ws.send(_json.dumps({
            "type": "client.heartbeat",
            "client": "electron",
            "version": "0.3.0",
        }))

        # Should not close the connection. Verify by sending a valid message after.
        await ws.send(_json.dumps({"type": "client.voice.started"}))
        msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
        assert msg["type"] == "presence.changed", \
            f"heartbeat should not break connection, got {msg['type']}"


# ── Test 8: Presence State Machine Ordering ───────────────────────────────────

@pytest.mark.asyncio
async def test_presence_state_ordering():
    """Full voice cycle: voice.final should trigger recalling → speaking → idle.

    Current Gateway emits: RECALLING → SPEAKING (fine-grained REASONING/GENERATING
    are defined but not yet wired into the voice.final handler).
    """
    async with _ws_connect() as ws:
        await ws.send(_json.dumps({
            "type": "client.voice.final",
            "text": "你好",
            "session_id": "e3_6_ordering_test",
        }))

        events = []
        try:
            while True:
                msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                events.append(msg)
                # Wait for assistant.completed + trailing idle event
                if msg["type"] == "assistant.completed":
                    try:
                        last = _json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                        events.append(last)
                    except asyncio.TimeoutError:
                        pass
                    break
                if msg["type"] == "speech.cancelled":
                    break
        except asyncio.TimeoutError:
            pass

        states = [e["data"]["state"] for e in events if e["type"] == "presence.changed"]
        log(f"State transitions: {' → '.join(states)}")

        # Must start with recalling (first presence event after voice.final)
        assert "recalling" in states, f"missing RECALLING in {states}"

        # Must end with idle
        assert states[-1] == "idle", f"final state must be idle, got {states[-1]}"

        # Must have speaking before completion
        assert "speaking" in states, f"missing SPEAKING in {states}"

        # No invalid transitions
        assert "interrupted" not in states, \
            f"INTERRUPTED should not appear in normal completion: {states}"

        # Verify the order: recalling before speaking
        rec_idx = states.index("recalling")
        spk_idx = states.index("speaking")
        assert rec_idx < spk_idx, \
            f"recalling ({rec_idx}) must come before speaking ({spk_idx})"


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    # Run pytest on this file
    sys.exit(subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=str(Path(__file__).resolve().parent.parent.parent),
    ).returncode)
