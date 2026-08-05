#!/usr/bin/env python3
"""Julia Voice Loop v2.0 — E3.6 Local Voice Reality Test.

Validates the full Runtime body loop:
  Microphone → VAD → Google STT → JuliaSession → Edge TTS → Speaker
  With: Presence State Machine, Event Trace, Interrupt, Latency.

Usage:
  python scripts/voice_loop.py
  python scripts/voice_loop.py --trace-dir /tmp/julia-traces

Press Enter to speak. Ctrl+C during Julia's speech to interrupt.
Ctrl+C twice to exit.
"""

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

sys.path.insert(0, "/Users/admin/julia_ai_assistant")
sys.path.insert(0, "/Users/admin/julia_core")

# ── Config ────────────────────────────────────────────────────────────────────

SAMPLE_RATE = 16000
BLOCK_DURATION = 0.5
SILENCE_BLOCKS = 3
SILENCE_THRESHOLD = 0.012
MAX_DURATION = 12.0
TRACE_DIR = os.environ.get("JULIA_TRACE_DIR", str(Path.home() / ".julia/traces"))

# ── Interrupt State ───────────────────────────────────────────────────────────

_interrupted = threading.Event()
_current_playback: subprocess.Popen | None = None


def _on_playback_start(proc: subprocess.Popen):
    global _current_playback
    _current_playback = proc


def _on_interrupt(signum, frame):
    """SIGINT handler: first press = interrupt speech, second press = quit."""
    global _current_playback
    if _interrupted.is_set():
        # Second interrupt — hard quit
        print("\n  👋 Goodbye.")
        sys.exit(0)
    _interrupted.set()
    if _current_playback and _current_playback.poll() is None:
        _current_playback.terminate()
        _current_playback = None
    print("\n  ⏸  Interrupted — listening...")


signal.signal(signal.SIGINT, _on_interrupt)


# ── Audio Input ───────────────────────────────────────────────────────────────


def record_until_silence(device=1) -> bytes | None:
    """Record from microphone. Auto-stop after 1.5s silence or 12s max."""
    _interrupted.clear()
    chunks = []
    silent_blocks = 0
    block_samples = int(SAMPLE_RATE * BLOCK_DURATION)
    total_samples = 0
    max_samples = int(SAMPLE_RATE * MAX_DURATION)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                        device=device, blocksize=block_samples) as stream:
        while total_samples < max_samples:
            if _interrupted.is_set():
                return None
            audio, _ = stream.read(block_samples)
            audio_f32 = audio.flatten().astype(np.float64)
            chunks.append(audio_f32.copy())
            total_samples += block_samples
            rms = float(np.sqrt(np.mean(audio_f32 ** 2)))
            silent_blocks = 0 if rms >= SILENCE_THRESHOLD else silent_blocks + 1
            if silent_blocks >= SILENCE_BLOCKS:
                if len(chunks) > SILENCE_BLOCKS:
                    chunks = chunks[:-SILENCE_BLOCKS]
                break

    if len(chunks) < 2:
        return None
    audio_f32 = np.concatenate(chunks)
    return (audio_f32 * 32767).astype(np.int16).tobytes()


# ── STT ───────────────────────────────────────────────────────────────────────


def transcribe(audio_bytes: bytes) -> tuple[str, float]:
    """Transcribe audio to text. Returns (text, latency_seconds)."""
    t0 = time.time()
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name; tmp.close()
        with wave.open(tmp_path, "w") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SAMPLE_RATE)
            w.writeframes(audio_bytes)
        with sr.AudioFile(tmp_path) as source:
            audio = r.record(source)
        os.unlink(tmp_path)
        text = r.recognize_google(audio, language="zh-CN")
        return text, time.time() - t0
    except Exception:
        return "", time.time() - t0


# ── Julia Session ─────────────────────────────────────────────────────────────


def chat(text: str) -> str:
    """Route through JuliaSession — same as Gateway /chat and WS /ws endpoints."""
    from julia_core.runtime.julia_session import get_session
    return get_session().chat(text)


# ── Voice Expression Filter ───────────────────────────────────────────────────


def _strip_stage_directions(text: str) -> str:
    """Remove parenthetical stage directions from TTS output."""
    text = re.sub(r'[（(][^)）]{2,}[)）]', '', text)
    text = re.sub(r' +', ' ', text).strip()
    return text


# ── TTS ───────────────────────────────────────────────────────────────────────


def speak(text: str) -> float | None:
    """Speak text via Edge TTS. Returns latency from call to first audio, or None.

    Playback runs in a subprocess so SIGINT can terminate it (interrupt).
    """
    if not text:
        return None
    voice_text = _strip_stage_directions(text)
    if not voice_text:
        return None

    t0 = time.time()
    try:
        import edge_tts
        import asyncio as _asyncio

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name

        async def _gen():
            comm = edge_tts.Communicate(voice_text, "zh-CN-XiaoxiaoNeural",
                                        rate="-10%", pitch="+0Hz")
            await comm.save(tmp_path)

        _asyncio.run(_gen())

        gen_latency = time.time() - t0

        # Play with afplay — can be terminated for interrupt
        proc = subprocess.Popen(["afplay", tmp_path])
        _on_playback_start(proc)
        proc.wait()
        _on_playback_start(None)
        os.unlink(tmp_path)

        if proc.returncode == -15:  # SIGTERM — interrupted
            return gen_latency
        return gen_latency
    except Exception:
        return None


# ── E3.6 Runtime Instrumentation ──────────────────────────────────────────────


class VoiceTrace:
    """E3.6 structured trace for voice interactions. Records every event with timing."""

    def __init__(self):
        self.events: list[dict] = []
        self._start = time.time()
        self._seq = 0

    def record(self, event_type: str, data: dict | None = None):
        self._seq += 1
        self.events.append({
            "seq": self._seq,
            "t_ms": int((time.time() - self._start) * 1000),
            "event": event_type,
            "data": data or {},
        })

    def summary(self) -> str:
        lines = [f"Trace ({len(self.events)} events, {self.elapsed_ms()}ms)"]
        for e in self.events:
            lines.append(f"  [{e['t_ms']:>5}ms] {e['event']}")
        return "\n".join(lines)

    def elapsed_ms(self) -> int:
        return int((time.time() - self._start) * 1000)

    def save(self, trace_id: str = ""):
        Path(TRACE_DIR).mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%H%M%S")
        path = Path(TRACE_DIR) / f"voice_trace_{ts}.jsonl"
        with open(path, "w") as f:
            for e in self.events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        return str(path)


def run_e3_6_test(trace: VoiceTrace) -> dict:
    """Run one full voice interaction cycle with Runtime instrumentation.

    Returns:
      {
        "transcript": str,      # what Tony said
        "reply": str,           # what Julia replied
        "stt_latency_ms": int,
        "llm_latency_ms": int,
        "tts_latency_ms": int,
        "interrupted": bool,
        "presence_states": [str],
      }
    """
    from julia_core.runtime.presence.state_machine import get_presence, PresenceState
    pm = get_presence()
    presence_states = []

    def _record_presence(state):
        presence_states.append(state.value if hasattr(state, 'value') else str(state))

    result = {
        "transcript": "",
        "reply": "",
        "stt_latency_ms": 0,
        "llm_latency_ms": 0,
        "tts_latency_ms": 0,
        "interrupted": False,
        "presence_states": presence_states,
    }

    # ── Phase 1: Listen ──
    trace.record("client.voice.started")
    pm.transition(PresenceState.LISTENING)
    _record_presence(pm.state)

    audio = record_until_silence()
    if audio is None or len(audio) < 1000:
        trace.record("client.voice.cancelled", {"reason": "no_speech" if audio is None else "interrupted"})
        pm.transition(PresenceState.IDLE)
        return result

    trace.record("client.voice.final", {"audio_bytes": len(audio)})

    # ── Phase 2: Transcribe ──
    text, stt_latency = transcribe(audio)
    result["stt_latency_ms"] = int(stt_latency * 1000)
    trace.record("stt.completed", {"text": text, "latency_ms": result["stt_latency_ms"]})

    if not text:
        trace.record("stt.empty")
        pm.transition(PresenceState.IDLE)
        return result

    result["transcript"] = text
    print(f"  💬 Tony: {text}", flush=True)

    # ── Phase 3: Recall + Think ──
    pm.transition(PresenceState.RECALLING)
    _record_presence(pm.state)
    trace.record("runtime.recalling")

    t_llm_start = time.time()

    pm.transition(PresenceState.REASONING)
    _record_presence(pm.state)
    trace.record("runtime.reasoning")

    reply = chat(text)
    result["llm_latency_ms"] = int((time.time() - t_llm_start) * 1000)
    trace.record("assistant.completed", {"reply": reply[:100], "latency_ms": result["llm_latency_ms"]})

    if not reply:
        trace.record("assistant.empty")
        pm.transition(PresenceState.IDLE)
        return result

    result["reply"] = reply
    print(f"  💬 Julia: {reply}", flush=True)

    # Check for interrupt before speaking
    if _interrupted.is_set():
        trace.record("speech.cancelled", {"reason": "interrupted_before_speech"})
        pm.transition(PresenceState.LISTENING)
        _record_presence(pm.state)
        result["interrupted"] = True
        return result

    # ── Phase 4: Speak ──
    pm.transition(PresenceState.GENERATING)
    _record_presence(pm.state)
    trace.record("speech.request", {"text_preview": reply[:80]})

    pm.transition(PresenceState.SPEAKING)
    _record_presence(pm.state)

    t_tts_start = time.time()
    tts_latency = speak(reply)
    if tts_latency is not None:
        result["tts_latency_ms"] = int(tts_latency * 1000)

    if _interrupted.is_set():
        trace.record("speech.cancelled", {"reason": "user_interrupt", "latency_ms": result["tts_latency_ms"]})
        _interrupted.clear()
        pm.transition(PresenceState.LISTENING)
        _record_presence(pm.state)
        result["interrupted"] = True
    else:
        trace.record("speech.completed")
        pm.transition(PresenceState.IDLE)
        _record_presence(pm.state)

    return result


# ── Latency Report ─────────────────────────────────────────────────────────────


def print_latency_report(session_results: list[dict]):
    """Print cumulative latency stats for the session."""
    if not session_results:
        return

    stt_times = [r["stt_latency_ms"] for r in session_results if r["stt_latency_ms"] > 0]
    llm_times = [r["llm_latency_ms"] for r in session_results if r["llm_latency_ms"] > 0]
    tts_times = [r["tts_latency_ms"] for r in session_results if r["tts_latency_ms"] > 0]
    interrupts = sum(1 for r in session_results if r["interrupted"])

    def _avg(vals): return int(sum(vals) / len(vals)) if vals else 0

    print(f"""
  ┌─ Latency Report ({len(session_results)} turns, {interrupts} interrupts) ─────────────────┐
  │  STT (voice→text):     avg {_avg(stt_times):>5}ms  min {min(stt_times) if stt_times else 0:>5}ms  max {max(stt_times) if stt_times else 0:>5}ms │
  │  LLM (text→reply):     avg {_avg(llm_times):>5}ms  min {min(llm_times) if llm_times else 0:>5}ms  max {max(llm_times) if llm_times else 0:>5}ms │
  │  TTS (reply→audio):    avg {_avg(tts_times):>5}ms  min {min(tts_times) if tts_times else 0:>5}ms  max {max(tts_times) if tts_times else 0:>5}ms │
  │  End-to-end:           avg {_avg([r['stt_latency_ms']+r['llm_latency_ms']+r['tts_latency_ms'] for r in session_results if r['transcript']]):>5}ms                            │
  └─────────────────────────────────────────────────────────────────────┘\
""")


# ── Main ───────────────────────────────────────────────────────────────────────


def main():
    print("Julia Voice Loop v2.0 — E3.6 Local Voice Reality Test")
    print(f"  ASR: Google Speech Recognition")
    print(f"  LLM: JuliaSession.chat() (DeepSeek via Provider)")
    print(f"  TTS: Edge TTS (zh-CN-XiaoxiaoNeural)")
    print(f"  Trace: {TRACE_DIR}")
    print()
    print("  ⌨  Press Enter to speak")
    print("  🛑 Ctrl+C during Julia's speech to interrupt")
    print("  🛑 Ctrl+C twice to exit")
    print()

    session_results: list[dict] = []
    turn = 0

    try:
        while True:
            input("  ➤ Press Enter to talk...")

            trace = VoiceTrace()
            trace.record("turn.start", {"turn": turn})

            result = run_e3_6_test(trace)
            session_results.append(result)

            if result["transcript"]:
                turn += 1
                trace.record("turn.end", {
                    "turn": turn,
                    "interrupted": result["interrupted"],
                    "total_ms": trace.elapsed_ms(),
                })
                trace.save()

                # Print trace summary for this turn
                states = " → ".join(result["presence_states"])
                print(f"  📊 States: {states}", flush=True)
                if result["interrupted"]:
                    print(f"  ⚡ INTERRUPTED — speech cancelled, ready for new input", flush=True)

            print()

    except KeyboardInterrupt:
        print("\n")
        print_latency_report(session_results)
        print("  👋 Goodbye.")


if __name__ == "__main__":
    main()
