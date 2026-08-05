"""Runtime Event Trace — observability for Julia's nervous system.

Records every event flowing through the Gateway as a timeline.
Debugging tool for Voice, Tool, Memory, MCP, Robot interactions.
"""

from __future__ import annotations

import json as _json
import time as _time
from pathlib import Path
from typing import Optional

TRACE_DIR = Path("/Users/admin/.julia/traces")


class EventTrace:
    """One interaction trace — voice.started → ... → assistant.completed."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.events: list[dict] = []
        self._start = _time.time()

    def record(self, event_type: str, data: dict = None):
        self.events.append({
            "t": _time.strftime("%H:%M:%S.%f")[:-3],
            "event": event_type,
            "data": data or {},
        })

    def elapsed_ms(self) -> int:
        return int((_time.time() - self._start) * 1000)

    def summary(self) -> str:
        lines = [f"Trace {self.session_id} ({self.elapsed_ms()}ms)"]
        for e in self.events:
            lines.append(f"  [{e['t']}] {e['event']}")
        return "\n".join(lines)

    def save(self):
        TRACE_DIR.mkdir(parents=True, exist_ok=True)
        path = TRACE_DIR / f"trace_{self.session_id}_{_time.strftime('%H%M%S')}.jsonl"
        with open(path, "w") as f:
            for e in self.events:
                f.write(_json.dumps(e, ensure_ascii=False) + "\n")
        return str(path)


class TraceCollector:
    """Collects recent traces for inspection."""

    def __init__(self):
        self.recent: list[EventTrace] = []
        self._current: Optional[EventTrace] = None

    def start(self, session_id: str = "") -> EventTrace:
        self._current = EventTrace(session_id)
        return self._current

    def finish(self) -> Optional[EventTrace]:
        if self._current and self._current.elapsed_ms() > 0:
            self.recent.append(self._current)
            if len(self.recent) > 50:
                self.recent = self.recent[-50:]
            trace = self._current
            self._current = None
            return trace
        self._current = None
        return None

    def list_recent(self, n: int = 10) -> list[dict]:
        return [{"session_id": t.session_id, "events": len(t.events),
                 "duration_ms": t.elapsed_ms(), "summary": t.summary()}
                for t in self.recent[-n:]]


# ── Singleton ───────────────────────────────────────────────────────────────

_collector: Optional[TraceCollector] = None


def get_collector() -> TraceCollector:
    global _collector
    if _collector is None:
        _collector = TraceCollector()
    return _collector
