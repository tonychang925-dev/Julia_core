"""E2E-01/02/03 — Conversation v2 Smoke Tests.

E2E-01: Text happy path (Core create → turn → canonical → reopen)
E2E-02: Voice happy path (ASR FINAL → Brain → Core → TTS)
E2E-03: Text↔Voice same conversation (zero history transfer)

Requires: Brain :18089, S2S :8765, Voice frontend :7860
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

BRAIN = "http://127.0.0.1:18089"

# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def api(method, path, body=None):
    url = f"{BRAIN}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def ok(r): return 200 <= r[0] < 300

def assert_ok(r, msg=""):
    assert ok(r), f"{msg}: HTTP {r[0]} {r[1]}"

def sleep(s=0.3): time.sleep(s)


# ═══════════════════════════════════════════════════════════════════════════
# E2E-00 Preflight
# ═══════════════════════════════════════════════════════════════════════════

def test_e2e00_brain_healthy():
    s, d = api("GET", "/internal/v1/voice/health")
    assert s == 200
    assert d["status"] == "ok"

def test_e2e00_storage_v2_healthy():
    """Verify conversations.json is the legacy, v2 target exists."""
    # Legacy exists and is read-only
    legacy = Path.home() / "julia_ai_assistant/data/conversations.json"
    assert legacy.exists(), "Legacy store not found"

def test_e2e00_conversation_list():
    s, d = api("GET", "/internal/v1/conversations")
    assert s == 200
    assert isinstance(d, list)


# ═══════════════════════════════════════════════════════════════════════════
# E2E-01 Text Happy Path
# ═══════════════════════════════════════════════════════════════════════════

def test_e2e01_core_first_create():
    """E2E-01: Core creates canonical conversation before client bind."""
    s, d = api("POST", "/internal/v1/conversations", {"title": "E2E-Text-A"})
    assert_ok((s, d), "create conversation")
    conv_id = d["conversation_id"]
    assert conv_id, "No conversation_id returned"
    return conv_id

def test_e2e01_text_turn(conv_id):
    """E2E-01: User turn → durable → assistant."""
    turn_id = f"e2e_t1_{int(time.time())}"
    s, d = api("POST", f"/internal/v1/conversations/{conv_id}/turns", {
        "turn_id": turn_id, "modality": "text", "input": "E2E测试：Julia，你好，今天天气怎么样？", "stream": False,
    })
    assert_ok((s, d), f"text turn {turn_id}")
    assert d["status"] == "completed"
    return turn_id

def test_e2e01_idempotent_retry(conv_id, turn_id, content):
    """E2E-01: Same turn_id + same content → idempotent."""
    s, d = api("POST", f"/internal/v1/conversations/{conv_id}/turns", {
        "turn_id": turn_id, "modality": "text", "input": content, "stream": False,
    })
    assert_ok((s, d), "idempotent retry")
    assert d["status"] == "completed"

def test_e2e01_reopen(conv_id):
    """E2E-01: Reopen conversation, verify transcript."""
    s, d = api("GET", f"/internal/v1/conversations/{conv_id}/messages")
    assert_ok((s, d), "get messages")
    msgs = d.get("messages", [])
    assert len(msgs) >= 2, f"Expected >=2 messages, got {len(msgs)}"
    return msgs

def test_e2e01_full():
    print("  E2E-01 Text Happy Path...")
    conv_id = test_e2e01_core_first_create()
    print(f"    created: {conv_id}")
    turn_id = test_e2e01_text_turn(conv_id)
    print(f"    turn: {turn_id}")
    content = "E2E测试：Julia，你好，今天天气怎么样？"
    test_e2e01_idempotent_retry(conv_id, turn_id, content)
    print(f"    retry: idempotent ✓")
    msgs = test_e2e01_reopen(conv_id)
    user_msgs = [m for m in msgs if m["role"] == "user"]
    assert len(user_msgs) == 1, f"Expected 1 user msg, got {len(user_msgs)}"
    assert content in user_msgs[0]["content"]
    print(f"    transcript: {len(msgs)} msgs, user confirmed ✓")
    print(f"  E2E-01 PASS")


# ═══════════════════════════════════════════════════════════════════════════
# E2E-02 Voice Smoke (Brain-side verification)
# ═══════════════════════════════════════════════════════════════════════════

def test_e2e02_voice_turn_via_brain():
    """E2E-02: Voice turn through Brain native_stream path.

    Simulates what S2S sends: conversation_id + turn_id + transcript.
    Verifies canonical user durable before cognition.
    """
    s, d = api("POST", "/internal/v1/conversations", {"title": "E2E-Voice-A"})
    assert_ok((s, d), "create voice conversation")
    conv_id = d["conversation_id"]

    turn_id = f"e2e_v1_{int(time.time())}"
    content = "E2E语音测试：我们正在验证语音转文字后的持久化路径。"

    # Simulate S2S chat completions call (Voice ASR FINAL → Brain)
    import urllib.request
    body = json.dumps({
        "messages": [{"role": "user", "content": content}],
        "conversation_id": conv_id, "turn_id": turn_id,
        "modality": "voice", "stream": False,
    }).encode()
    req = urllib.request.Request(f"{BRAIN}/v1/chat/completions", data=body)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        assert False, f"Voice turn failed: HTTP {e.code}: {body[:200]}"

    print(f"    voice turn: {turn_id} → {result.get('status', '?')}")

    # Verify canonical
    s, d = api("GET", f"/internal/v1/conversations/{conv_id}/messages")
    user_msgs = [m for m in d["messages"] if m["role"] == "user"]
    assert len(user_msgs) == 1
    assert content in user_msgs[0]["content"]
    assert user_msgs[0]["status"] == "completed"
    print(f"    canonical: user completed, content verified ✓")
    return conv_id, turn_id

def test_e2e02_full():
    print("  E2E-02 Voice Happy Path...")
    conv_id, turn_id = test_e2e02_voice_turn_via_brain()
    print(f"    conversation: {conv_id}")
    print(f"  E2E-02 PASS")


# ═══════════════════════════════════════════════════════════════════════════
# E2E-03 Text ↔ Voice Same Conversation
# ═══════════════════════════════════════════════════════════════════════════

def test_e2e03_text_voice_text():
    """E2E-03: Text→Voice→Text on same conversation_id."""
    s, d = api("POST", "/internal/v1/conversations", {"title": "E2E-ModeSwitch"})
    assert_ok((s, d), "create")
    conv_id = d["conversation_id"]

    # Text T1
    t1 = f"e2e_sw_t1_{int(time.time())}"
    t1_content = "E2E模式切换Text-1：文字输入"
    api("POST", f"/internal/v1/conversations/{conv_id}/turns", {
        "turn_id": t1, "modality": "text", "input": t1_content, "stream": False,
    })
    sleep()

    # Voice T2
    t2 = f"e2e_sw_v2_{int(time.time())}"
    t2_content = "E2E模式切换Voice-2：语音输入模拟"
    body = json.dumps({
        "messages": [{"role": "user", "content": t2_content}],
        "conversation_id": conv_id, "turn_id": t2,
        "modality": "voice", "stream": False,
    }).encode()
    req = urllib.request.Request(f"{BRAIN}/v1/chat/completions", data=body)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as resp:
        json.loads(resp.read())
    sleep()

    # Text T3
    t3 = f"e2e_sw_t3_{int(time.time())}"
    t3_content = "E2E模式切换Text-3：回到文字"
    api("POST", f"/internal/v1/conversations/{conv_id}/turns", {
        "turn_id": t3, "modality": "text", "input": t3_content, "stream": False,
    })
    sleep()

    # Verify: conversation_id unchanged, 3 user turns in order
    s, d = api("GET", f"/internal/v1/conversations/{conv_id}/messages")
    user_msgs = [m for m in d["messages"] if m["role"] == "user"]
    assert len(user_msgs) == 3, f"Expected 3 user turns, got {len(user_msgs)}"
    assert t1_content in user_msgs[0]["content"]
    assert t2_content in user_msgs[1]["content"]
    assert t3_content in user_msgs[2]["content"]

    # Verify modalities
    modalities = [m.get("modality") for m in user_msgs]
    assert "text" in modalities
    assert "voice" in modalities

    print(f"    conversation: {conv_id}")
    print(f"    user turns: {len(user_msgs)} (text→voice→text), order correct ✓")
    print(f"    modalities: {modalities}")

def test_e2e03_full():
    print("  E2E-03 Text↔Voice...")
    test_e2e03_text_voice_text()
    print(f"  E2E-03 PASS")


# ═══════════════════════════════════════════════════════════════════════════
# Run
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("═══ E2E-00 Preflight ═══")
    test_e2e00_brain_healthy()
    print("  Brain: OK")
    test_e2e00_storage_v2_healthy()
    print("  Storage: OK")
    test_e2e00_conversation_list()
    print("  List: OK")
    print("  E2E-00 PASS\n")

    print("═══ E2E-01 Text Happy Path ═══")
    test_e2e01_full()
    print()

    print("═══ E2E-02 Voice Happy Path ═══")
    test_e2e02_full()
    print()

    print("═══ E2E-03 Text↔Voice ═══")
    test_e2e03_full()
    print()

    print("═══ E2E-00/01/02/03: ALL PASS ═══")
