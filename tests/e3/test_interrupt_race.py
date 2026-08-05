"""E3.5 Interrupt Race Test — validates Cancellation Convergence.

Contract: ADR-029 (Runtime Action Execution Model)
         docs/architecture/ADR-029_Runtime_Action_Execution_Model_v1.md

Tests the most failure-prone interrupt scenarios:
  1. Interrupt during LLM execution (run_in_executor)
  2. Interrupt during speech chunk streaming
  3. Race: fast LLM response + immediate interrupt
  4. Critical assertion: no speech.chunk(old) after voice.final(new)
"""

from __future__ import annotations

import asyncio
import json as _json
import time as _time
from dataclasses import dataclass, field

import pytest


# ── Simulated Gateway Components ──────────────────────────────────────────

@dataclass
class SimulatedPresence:
    """Minimal PresenceMachine for testing — mirrors state_machine.py contract."""
    state: str = "idle"
    previous: str = ""
    interrupted: bool = False

    _INTERRUPTIBLE = {"speaking", "generating", "recalling", "reasoning"}

    def is_interruptible(self) -> bool:
        return self.state in self._INTERRUPTIBLE

    def transition(self, new_state: str) -> dict:
        self.previous = self.state
        self.state = new_state
        return {"type": "presence.changed",
                "data": {"state": new_state, "previous": self.previous},
                "timestamp": _time.strftime("%H:%M:%S")}


# ── Test Action: Simulated Speech ────────────────────────────────────────

class SpeechAction:
    """Simulates the _process_reply() coroutine in gateway_server.py."""

    def __init__(self, llm_latency: float = 0.1, chunk_count: int = 5):
        self.llm_latency = llm_latency
        self.chunk_count = chunk_count
        self.events: list[dict] = []
        self.speech_id = f"sp-{int(_time.time()*1000)}"
        self._cancelled = False

    async def execute(self, pm: SimulatedPresence) -> str:
        """Full action execution: LLM → speech.request → chunks → completed."""
        try:
            # ── Phase 1: LLM generation (run_in_executor simulation) ──
            self.events.append({"type": "action.started", "phase": "llm.generate"})
            await asyncio.sleep(self.llm_latency)  # simulate LLM work

            # Check interrupt after LLM returns
            if pm.interrupted:
                raise asyncio.CancelledError()

            # ── Phase 2: Speech output ──
            self.events.append({"type": "presence.changed", "state": "speaking"})
            self.events.append({"type": "speech.request", "speech_id": self.speech_id})

            for i in range(self.chunk_count):
                if pm.interrupted:
                    raise asyncio.CancelledError()
                await asyncio.sleep(0.01)  # simulate chunk send
                self.events.append({"type": "speech.chunk", "sequence": i,
                                    "speech_id": self.speech_id})

            # ── Phase 3: Completion ──
            self.events.append({"type": "speech.completed", "speech_id": self.speech_id})
            self.events.append({"type": "assistant.completed"})
            return "completed"

        except asyncio.CancelledError:
            self._cancelled = True
            self.events.append({"type": "speech.cancelled",
                                "speech_id": self.speech_id,
                                "reason": "interrupted"})
            return "cancelled"


# ── Test Fixtures ────────────────────────────────────────────────────────

def event_types(events: list[dict]) -> list[str]:
    """Extract ordered event type names from event list."""
    return [e["type"] for e in events]


def chunks_for_speech_id(events: list[dict], speech_id: str) -> list[dict]:
    """Return all speech.chunk events for a given speech_id."""
    return [e for e in events
            if e["type"] == "speech.chunk" and e.get("speech_id") == speech_id]


# ── Test 1: Interrupt during LLM execution ───────────────────────────────

@pytest.mark.asyncio
async def test_interrupt_during_llm_execution():
    """voice.started arrives while LLM is still generating.

    Expected: speech.cancelled emitted, NO speech.chunk emitted.
    """
    pm = SimulatedPresence(state="listening")
    action = SpeechAction(llm_latency=0.5)  # slow LLM — 500ms

    # Start action in background
    task = asyncio.create_task(action.execute(pm))

    # Interrupt after 50ms — LLM still running
    await asyncio.sleep(0.05)
    pm.interrupted = True
    task.cancel()

    result = await task

    assert result == "cancelled"
    assert action._cancelled is True
    assert "speech.cancelled" in event_types(action.events)
    # Critical: no chunk was ever sent
    assert chunks_for_speech_id(action.events, action.speech_id) == []
    # No completed event
    assert "speech.completed" not in event_types(action.events)
    assert "assistant.completed" not in event_types(action.events)


# ── Test 2: Interrupt during speech chunk streaming ──────────────────────

@pytest.mark.asyncio
async def test_interrupt_during_chunk_streaming():
    """voice.started arrives mid-speech, during chunk streaming.

    Expected: speech.cancelled emitted. Some chunks may have been sent,
    but speech.completed must NOT appear.
    """
    pm = SimulatedPresence(state="listening")
    action = SpeechAction(llm_latency=0.01, chunk_count=10)  # fast LLM, many chunks

    task = asyncio.create_task(action.execute(pm))

    # Let LLM finish and first 2 chunks send
    await asyncio.sleep(0.04)  # LLM(10ms) + 2 chunks(10ms each) ≈ 30ms
    pm.interrupted = True
    task.cancel()

    result = await task

    assert result == "cancelled"
    assert "speech.cancelled" in event_types(action.events)
    assert "speech.completed" not in event_types(action.events)
    assert "assistant.completed" not in event_types(action.events)

    # Some chunks may have been sent before cancellation — but not all
    sent_chunks = chunks_for_speech_id(action.events, action.speech_id)
    assert len(sent_chunks) < action.chunk_count


# ── Test 3: Race — fast LLM + immediate interrupt ────────────────────────

@pytest.mark.asyncio
async def test_fast_llm_immediate_interrupt():
    """The hardest case: LLM responds very fast, user interrupts almost immediately.

    This is the scenario that BROKE the old flag-based approach.
    With task.cancel(), the CancelledError propagates through the await chain.
    """
    pm = SimulatedPresence(state="listening")
    action = SpeechAction(llm_latency=0.001, chunk_count=3)  # extremely fast LLM

    task = asyncio.create_task(action.execute(pm))

    # Interrupt nearly instantly
    await asyncio.sleep(0.002)
    pm.interrupted = True
    task.cancel()

    result = await task

    assert result == "cancelled"
    assert "speech.cancelled" in event_types(action.events)
    # speech.completed must NOT appear, even though LLM was fast
    assert "speech.completed" not in event_types(action.events)


# ── Test 4: Critical assertion — no old chunk after new question ─────────

@pytest.mark.asyncio
async def test_no_old_chunk_after_new_voice_final():
    """After interrupt + new voice.final, old speech.chunk must NOT appear.

    Scenario:
      T0: voice.final("分析一下市场")
      T1: speech.chunk[0] ← old question
      T2: voice.started (user interrupts)
      T3: speech.cancelled ← old
      T4: voice.final("我想问另一个问题") ← new question
      T5: speech.chunk[0] ← NEW question only

    Critical assertion: T5's speech_id != T1's speech_id.
    """
    events_log: list[dict] = []

    # ── First question ──
    pm = SimulatedPresence(state="listening")
    action1 = SpeechAction(llm_latency=0.05, chunk_count=5)
    action1.speech_id = "sp-old"

    task1 = asyncio.create_task(action1.execute(pm))

    # Let first chunk send
    await asyncio.sleep(0.07)  # LLM(50ms) + 1 chunk(10ms)

    # User interrupts
    pm.interrupted = True
    task1.cancel()
    await task1

    events_log.extend(action1.events)

    # ── Second question ──
    pm.interrupted = False
    pm.state = "listening"
    action2 = SpeechAction(llm_latency=0.02, chunk_count=3)
    action2.speech_id = "sp-new"

    task2 = asyncio.create_task(action2.execute(pm))
    await task2

    events_log.extend(action2.events)

    # ── Assertions ──
    old_chunks = chunks_for_speech_id(events_log, "sp-old")
    new_chunks = chunks_for_speech_id(events_log, "sp-new")

    # Old question was cancelled
    assert any(e["type"] == "speech.cancelled" and e["speech_id"] == "sp-old"
               for e in events_log), "Old speech must be cancelled"

    # New question completed
    assert any(e["type"] == "speech.completed" and e["speech_id"] == "sp-new"
               for e in events_log), "New speech must complete"

    # CRITICAL: all old chunks appear BEFORE any new chunk
    if old_chunks and new_chunks:
        old_chunk_indices = [events_log.index(c) for c in old_chunks]
        new_chunk_indices = [events_log.index(c) for c in new_chunks]
        assert max(old_chunk_indices) < min(new_chunk_indices), \
            "Old speech.chunk MUST NOT appear after new question's speech.chunk"

    # CRITICAL: speech.cancelled(old) appears before speech.request(new)
    cancel_events = [i for i, e in enumerate(events_log)
                     if e["type"] == "speech.cancelled" and e["speech_id"] == "sp-old"]
    request_events = [i for i, e in enumerate(events_log)
                      if e["type"] == "speech.request" and e["speech_id"] == "sp-new"]
    if cancel_events and request_events:
        assert cancel_events[0] < request_events[0], \
            "speech.cancelled(old) MUST appear before speech.request(new)"


# ── Test 5: Normal completion (no interrupt) ─────────────────────────────

@pytest.mark.asyncio
async def test_normal_completion_without_interrupt():
    """Baseline: without interruption, action completes normally."""
    pm = SimulatedPresence(state="listening")
    action = SpeechAction(llm_latency=0.01, chunk_count=3)

    result = await action.execute(pm)

    assert result == "completed"
    assert action._cancelled is False
    assert "speech.request" in event_types(action.events)
    assert "speech.chunk" in event_types(action.events)
    assert "speech.completed" in event_types(action.events)
    assert "assistant.completed" in event_types(action.events)
    assert "speech.cancelled" not in event_types(action.events)


# ── Test 6: Double interrupt — second voice.started during cancellation ───

@pytest.mark.asyncio
async def test_double_interrupt_is_idempotent():
    """Second voice.started during cancellation should be a no-op."""
    pm = SimulatedPresence(state="speaking")
    action = SpeechAction(llm_latency=0.1, chunk_count=5)

    task = asyncio.create_task(action.execute(pm))

    await asyncio.sleep(0.02)
    pm.interrupted = True
    task.cancel()  # first cancel

    # Second cancel immediately — should not raise
    pm.interrupted = True
    if not task.done():
        task.cancel()  # idempotent: cancelling already-cancelling task is safe

    result = await task

    assert result == "cancelled"
    # Only one speech.cancelled event
    cancel_count = sum(1 for e in action.events if e["type"] == "speech.cancelled")
    assert cancel_count == 1, f"Expected 1 speech.cancelled, got {cancel_count}"
