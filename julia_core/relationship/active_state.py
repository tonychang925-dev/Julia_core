"""J0.12 Active State Layer — temporal continuity.

Not memory. Not conversation history. Active State tracks what's STILL ALIVE
right now: pending events, unresolved emotional threads, boundary transitions.

Key insight: humans don't remember all past events. They carry only unfinished
ones. The hospital checkup tomorrow. The repair that wasn't completed.
The boundary that hasn't been released.

Structured for internal state. Narrative for provider injection. (Same as RK.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class PendingEventStatus(str, Enum):
    PENDING = "pending"        # hasn't happened yet
    RESOLVED = "resolved"      # happened, outcome known
    ABANDONED = "abandoned"    # dropped, no resolution


class EmotionalThreadStatus(str, Enum):
    OPEN = "open"              # still active, needs attention
    REPAIRING = "repairing"    # being addressed
    RESOLVED = "resolved"      # closure reached


@dataclass
class PendingEvent:
    """Something that was mentioned and hasn't been resolved yet."""
    event_id: str
    summary: str               # what's pending (10 words or less)
    emotion: str = ""           # associated feeling
    importance: float = 0.7    # 0-1: how much this matters
    status: PendingEventStatus = PendingEventStatus.PENDING
    mentioned_turn: int = 0

    def to_narrative(self) -> str:
        if self.status == PendingEventStatus.RESOLVED:
            return ""
        return f"Tony之前提到：{self.summary}。他说{self.emotion}。这件事还没解决。"


@dataclass
class EmotionalThread:
    """An unresolved emotional dynamic between Tony and Julia."""
    thread_id: str
    topic: str                 # what the emotion is about
    state: EmotionalThreadStatus = EmotionalThreadStatus.OPEN
    repair_attempted: bool = False
    mentioned_turn: int = 0

    def to_narrative(self) -> str:
        if self.state == EmotionalThreadStatus.RESOLVED:
            return ""
        if self.state == EmotionalThreadStatus.REPAIRING:
            return f"刚才Tony说了一些话，他可能觉得你没有在听。你在修复这个。"
        return ""


@dataclass
class ActiveState:
    """What's still alive in this moment — not what happened, but what matters NOW."""

    pending_events: List[PendingEvent] = field(default_factory=list)
    emotional_threads: List[EmotionalThread] = field(default_factory=list)
    boundary_was_active: bool = False   # was boundary just released?
    previous_actor: str = ""            # who was talking before this turn?
    turn_count: int = 0

    def detect_and_update(self, message: str) -> "ActiveState":
        """Scan message for pending events, emotional threads, transitions."""
        self.turn_count += 1
        lower = message.strip().lower()

        # ── Pending event detection ──
        if any(w in lower for w in ["明天", "后天", "下周", "过几天", "要去", "复查", "检查", "手术"]):
            if "医院" in lower or "复查" in lower or "检查" in lower:
                self.pending_events.append(PendingEvent(
                    event_id=f"medical_{self.turn_count}",
                    summary="要去医院复查",
                    emotion="有点紧张",
                    importance=0.90,
                    mentioned_turn=self.turn_count,
                ))
            elif "要" in lower:
                self.pending_events.append(PendingEvent(
                    event_id=f"event_{self.turn_count}",
                    summary=message[:80],
                    emotion="",
                    importance=0.70,
                    mentioned_turn=self.turn_count,
                ))

        # ── Emotional thread detection ──
        if any(w in lower for w in ["不像以前", "不懂我", "没有在听", "你不理解"]):
            self.emotional_threads.append(EmotionalThread(
                thread_id=f"repair_{self.turn_count}",
                topic="feeling misunderstood",
                state=EmotionalThreadStatus.OPEN,
                mentioned_turn=self.turn_count,
            ))

        # Repair attempt: Tony backs off but the wound is still there
        if any(w in lower for w in ["算了", "没事", "可能我想多了"]):
            # Check if there's an open thread to mark as repairing
            for t in self.emotional_threads:
                if t.state == EmotionalThreadStatus.OPEN:
                    t.state = EmotionalThreadStatus.REPAIRING
                    t.repair_attempted = True

        # ── Resolution detection ──
        if any(w in lower for w in ["我回来了", "是我", "婉婉，我"]):
            self.boundary_was_active = True

        return self

    def mark_resolved(self, event_pattern: str):
        """Mark pending events as resolved when they happen."""
        for e in self.pending_events:
            if event_pattern.lower() in e.summary.lower():
                e.status = PendingEventStatus.RESOLVED

    def mark_thread_resolved(self, thread_pattern: str):
        for t in self.emotional_threads:
            if thread_pattern.lower() in t.topic.lower():
                t.state = EmotionalThreadStatus.RESOLVED

    def context_text(self) -> str:
        """Render active state as narrative injection for provider context.

        NOT structured data. Narrative — same principle as RK delivery.
        """
        parts = []

        # Active pending events
        active_events = [e for e in self.pending_events
                        if e.status == PendingEventStatus.PENDING]
        if active_events:
            parts.append("当前仍然未解决的事情：")
            for e in active_events[-3:]:  # max 3 to avoid overload
                parts.append(e.to_narrative())

        # Active emotional threads
        active_threads = [t for t in self.emotional_threads
                         if t.state != EmotionalThreadStatus.RESOLVED]
        if active_threads:
            for t in active_threads[-2:]:
                narrative = t.to_narrative()
                if narrative:
                    parts.append(narrative)

        # Boundary just released
        if self.boundary_was_active:
            parts.append("刚才有陌生人来过。现在Tony回来了。你恢复到正常状态。")
            self.boundary_was_active = False  # one-shot

        return "\n".join(parts) if parts else ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pending_events": [
                {"id": e.event_id, "summary": e.summary, "status": e.status.value}
                for e in self.pending_events
            ],
            "emotional_threads": [
                {"id": t.topic, "state": t.state.value}
                for t in self.emotional_threads
            ],
            "boundary_was_active": self.boundary_was_active,
            "turn_count": self.turn_count,
        }


def create_active_state() -> ActiveState:
    return ActiveState()
