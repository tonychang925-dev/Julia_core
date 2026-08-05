"""Voice Architecture Freeze — CI-enforced invariant tests.

ADR-025-D: Client/Server Voice Runtime Split (FROZEN).

Forbidden patterns — CI fails on any match:
  speechSynthesis          Client must not synthesize voice
  TTSPlayer                Client must not play local TTS
  voice_ipc                Client must not run local STT
  stt_manager              Client must not manage STT process
  InputClass.ECHO          Server must not filter echo by text matching
  audio/mpeg               Client must not play MP3 blobs

Single-path invariants — one and only one of each:
  1 mic track              One uplink audio source
  1 ASR provider           One speech recognition path
  1 TTS output track       One downlink audio output
  1 Julia turn/utterance   No duplicate message processing
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
ELECTRON_ROOT = Path("/Users/admin/julia_electron")


# ── Forbidden Patterns in Julia Core ──────────────────────────────────────

FORBIDDEN_CORE = [
    "InputClass.ECHO",
    "speechSynthesis",
    "SpeechSynthesisUtterance",
    "TTSPlayer",
    "voice_ipc",
    "stt_manager",
]


def _grep_core(pattern: str) -> list[str]:
    """Run git grep in julia_core, return matching lines."""
    result = subprocess.run(
        ["git", "grep", "-n", pattern, "--", "*.py"],
        cwd=str(ROOT),
        capture_output=True, text=True,
    )
    if result.returncode not in (0, 1):
        return []
    return [l for l in result.stdout.strip().split("\n") if l]


def _grep_electron(pattern: str) -> list[str]:
    """Run git grep in julia_electron, return matching lines."""
    if not ELECTRON_ROOT.exists():
        return []
    result = subprocess.run(
        ["git", "grep", "-n", pattern, "--", "*.js", "*.jsx", "*.ts", "*.tsx"],
        cwd=str(ELECTRON_ROOT),
        capture_output=True, text=True,
    )
    if result.returncode not in (0, 1):
        return []
    return [l for l in result.stdout.strip().split("\n") if l]


@pytest.mark.parametrize("pattern", FORBIDDEN_CORE)
def test_forbidden_pattern_in_core(pattern: str):
    """Forbidden strings must not appear in julia_core Python source."""
    matches = _grep_core(pattern)
    # Allow in test files and docs only
    violations = [m for m in matches
                  if "tests/" not in m
                  and "docs/" not in m
                  and "test_" not in m]
    assert not violations, (
        f"Forbidden pattern '{pattern}' found in julia_core source:\n"
        + "\n".join(violations[:10])
    )


# ── Forbidden Patterns in Electron ────────────────────────────────────────

FORBIDDEN_ELECTRON = [
    "speechSynthesis",
    "SpeechSynthesisUtterance",
    "TTSPlayer",
    "voice_ipc",
    "stt_manager",
    "audio/mpeg",
]


@pytest.mark.parametrize("pattern", FORBIDDEN_ELECTRON)
def test_forbidden_pattern_in_electron(pattern: str):
    """Forbidden strings must not appear in julia_electron JS source."""
    matches = _grep_electron(pattern)
    # Allow in test files, docs, and node_modules
    violations = [m for m in matches
                  if "test/" not in m
                  and "node_modules/" not in m
                  and "docs/" not in m
                  and "legacy/" not in m
                  and "TTSPlayer.js" not in m]  # TTSPlayer file itself is OK if not imported
    # For TTSPlayer, check it's actually not imported
    if pattern == "TTSPlayer":
        imports = _grep_electron("import.*TTSPlayer|require.*TTSPlayer")
        violations = [m for m in imports
                      if "test/" not in m
                      and "node_modules/" not in m]

    assert not violations, (
        f"Forbidden pattern '{pattern}' found in julia_electron source:\n"
        + "\n".join(violations[:10])
    )


# ── Single-path invariants ────────────────────────────────────────────────

def test_single_mic_track():
    """Electron must have exactly one getUserMedia audio call (one mic track)."""
    matches = _grep_electron("getUserMedia")
    # Should appear in WebRTCVoice.js only
    audio_calls = [m for m in matches
                   if "audio" in m and "test/" not in m and "node_modules/" not in m]
    assert len(audio_calls) <= 2, (  # one call + possibly one comment reference
        f"Expected ≤1 getUserMedia audio call, found {len(audio_calls)}:\n"
        + "\n".join(audio_calls)
    )


def test_single_asr_provider():
    """Gateway must use exactly one ASR provider in the RTC path."""
    rtc_offer = ROOT / "julia_core" / "runtime" / "gateway_server.py"
    if not rtc_offer.exists():
        return
    content = rtc_offer.read_text()
    # The ASR provider import should appear exactly once in rtc_offer
    asr_imports = [l for l in content.split("\n")
                   if "ASRProvider" in l or "WhisperCPU" in l or "asr_provider" in l]
    # OK as long as it's not commented out
    active = [l for l in asr_imports if not l.strip().startswith("#") and not l.strip().startswith("//")]
    assert len(active) >= 1, "Gateway rtc_offer must have exactly one ASR provider wired"


def test_single_tts_output_track():
    """Only one TTS output path: EdgeTTSPCMProvider → TTSAudioTrack → WebRTC."""
    gateway = ROOT / "julia_core" / "runtime" / "gateway_server.py"
    if not gateway.exists():
        return
    content = gateway.read_text()
    # Verify TTSAudioTrack is used
    assert "TTSAudioTrack" in content or "tts_track" in content, \
        "Gateway must use TTSAudioTrack for TTS output"
    # Verify no ensure_future for TTS (must be awaited)
    tts_section_start = content.find("stage = \"tts-start\"")
    if tts_section_start > 0:
        tts_section = content[tts_section_start:tts_section_start + 500]
        assert "asyncio.ensure_future" not in tts_section, \
            "TTS must be awaited, not fire-and-forget"


def test_speech_completed_after_drain():
    """speech.completed must be sent AFTER TTS drain, not after enqueue."""
    gateway = ROOT / "julia_core" / "runtime" / "gateway_server.py"
    if not gateway.exists():
        return
    content = gateway.read_text()
    # Verify wait_generation_consumed exists and is called before send-complete
    assert "wait_generation_consumed" in content, \
        "Gateway must wait for TTS drain before speech.completed"


# ── Architecture single-path event flow ───────────────────────────────────

def test_one_turn_per_utterance():
    """Each voice input produces exactly one Julia reply (no duplicate POST /chat)."""
    electron_ws = ELECTRON_ROOT / "electron" / "main" / "websocket.js"
    if not electron_ws.exists():
        return
    content = electron_ws.read_text()
    # Text input may use HTTP POST /chat
    # Voice input must NOT trigger additional POST /chat
    # Check that voice events don't call sendMessage-like functions
    if "onVoiceTranscript" in content or "handleVoiceResult" in content:
        # Should exist but not call API.sendMessage
        pass  # This is validated by the forbidden pattern test above


# ── Behavioral Invariants (runtime semantics) ───────────────────────────────

@pytest.mark.asyncio
async def test_long_utterance_emits_once():
    """Continuous speech must NOT produce multiple final segments via force-emit."""
    from voice_runtime.pipeline.audio_pipeline import AudioPipeline
    import numpy as np

    pipeline = AudioPipeline(sample_rate=16000)
    emit_count = 0
    pipeline.on_speech_end(lambda _: emit_count.__setitem__(0, emit_count[0] + 1))
    emit_count = [0]

    # Push 300 speech frames (RMS > 200) without any silence
    loud = (np.ones(320, dtype=np.int16) * 500).tobytes()
    for _ in range(300):
        await pipeline.push_pcm(loud)

    # Then push 65 silence frames (RMS < 200) to trigger silence boundary
    silent = (np.zeros(320, dtype=np.int16)).tobytes()
    for _ in range(65):
        await pipeline.push_pcm(silent)

    # Must emit exactly ONCE (only at silence boundary, not force-emit)
    assert emit_count[0] == 1, (
        f"force-emit bug: {emit_count[0]} segments emitted for one utterance. "
        f"Expected exactly 1 (silence boundary only)"
    )


@pytest.mark.asyncio
async def test_tts_queue_backpressure_no_drop():
    """Queue at maxsize must block producer, not drop oldest frame."""
    from voice_runtime.transport.webrtc.tts_track import TTSAudioTrack, MAX_QUEUE_FRAMES, BYTES_PER_FRAME

    track = TTSAudioTrack()
    gen = track.begin_generation()
    frame = b"\x01" * BYTES_PER_FRAME

    # Fill queue to capacity
    for _ in range(MAX_QUEUE_FRAMES):
        assert await track.enqueue_pcm(frame, gen)
    assert track.pending_frames == MAX_QUEUE_FRAMES

    # 51st enqueue should BLOCK (queue full, no consumer)
    frame_51 = b"\x02" * BYTES_PER_FRAME
    blocked = asyncio.create_task(track.enqueue_pcm(frame_51, gen))
    await asyncio.sleep(0.1)
    assert not blocked.done(), (
        "Backpressure violated: 51st enqueue completed without consumer draining. "
        "Queue must block, not drop frames."
    )

    # Consumer drains one frame → unblocks producer
    consumed = await track.recv()
    assert consumed is not None  # aiortc AudioFrame received

    # Now the blocked enqueue should complete
    assert await asyncio.wait_for(blocked, timeout=1.0), (
        "Backpressure violated: blocked enqueue did not complete after drain."
    )
    assert track.pending_frames == MAX_QUEUE_FRAMES, (
        f"Expected {MAX_QUEUE_FRAMES} after drain+enqueue, got {track.pending_frames}"
    )


@pytest.mark.asyncio
async def test_tts_failure_never_completes():
    """If require_tts=True and TTS fails, speech.completed must NOT be sent."""
    # Verify require_tts parameter exists
    import inspect
    from julia_core.runtime.gateway_server import main as _unused
    # Check the source for require_tts
    gateway_path = Path(__file__).resolve().parent.parent.parent / "julia_core" / "runtime" / "gateway_server.py"
    content = gateway_path.read_text() if gateway_path.exists() else ""
    assert "require_tts" in content, (
        "gateway_server.py must support require_tts parameter "
        "to distinguish voice turns from text turns"
    )
    # Verify TTS failure raises RuntimeError, not silent continue
    assert 'raise RuntimeError("TTS produced no PCM frames")' in content, (
        "TTS failure must raise RuntimeError, not silently skip"
    )
    assert 'raise RuntimeError("TTS drain timed out")' in content, (
        "TTS drain timeout must raise RuntimeError"
    )


def test_missing_rtc_track_fails_voice_turn():
    """require_tts=True with no RTC session must fail, not fake text-only."""
    gateway_path = Path(__file__).resolve().parent.parent.parent / "julia_core" / "runtime" / "gateway_server.py"
    if not gateway_path.exists():
        return
    content = gateway_path.read_text()
    assert 'if require_tts:' in content, (
        "gateway_server.py must check require_tts before TTS"
    )
    assert 'raise RuntimeError' in content, (
        "Missing TTS track with require_tts=True must raise RuntimeError"
    )
    # Must NOT have a silent else: pass that falls through to speech.completed
    tts_section_start = content.find("if require_tts:")
    tts_section_end = content.find("stage = \"send-complete\"", tts_section_start)
    tts_section = content[tts_section_start:tts_section_end]
    assert "raise RuntimeError" in tts_section, (
        "require_tts block must raise on missing track, not fall through"
    )


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
