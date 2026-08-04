"""Julia Presence Journal — body state log.

NOT a user interaction log. NOT a memory system.
This is the body's heartbeat record — what Julia WAS doing, second by second.

Purpose:
  - Debug: "Why didn't Julia respond at 10:35?"
  - Health: track state transitions over time
  - Endurance: 24h test validation

Format:
  Timestamp | State | Duration | Trigger
  08:30:01  | idle  | 2h03m    | runtime.started
  10:33:15  | listening | 4.2s | voice.wake(婉婉)
  10:33:19  | thinking  | 3.1s | voice.final
  10:33:22  | speaking  | 8.5s | tts.speak
  10:33:31  | idle      | --   | tts.finished
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from voice_daemon.presence.manager import Presence

LOG_DIR = Path.home() / ".julia" / "presence"
LOG_RETENTION_DAYS = 30


class PresenceJournal:
    """Records every state transition with timestamp, duration, and trigger."""

    def __init__(self, log_dir=None):
        self._dir = Path(log_dir) if log_dir else LOG_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._current_file: Optional[Path] = None

    def _today_file(self) -> Path:
        return self._dir / f"presence_{datetime.now().strftime('%Y_%m_%d')}.jsonl"

    def record(self, new_state: Presence, old_state: Presence,
               trigger: str = "", duration_ms: float = 0.0):
        """Record a state transition. Called by PresenceManager on every change."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "new_state": new_state.value,
            "old_state": old_state.value,
            "duration_ms": round(duration_ms, 1),
            "trigger": trigger,
        }

        file = self._today_file()
        with open(file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def query(self, date_str: str = None) -> list[dict]:
        """Read presence log for a specific date (YYYY_MM_DD) or today."""
        file = self._dir / f"presence_{date_str or datetime.now().strftime('%Y_%m_%d')}.jsonl"
        if not file.exists():
            return []
        entries = []
        with open(file) as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return entries

    def today_summary(self) -> str:
        """Human-readable summary of today's presence activity."""
        entries = self.query()
        if not entries:
            return "今日无活动记录。"

        lines = [f"📊 Julia Presence — {datetime.now().strftime('%Y年%m月%d日')}"]
        lines.append("")

        # Count by state
        from collections import Counter
        counts = Counter(e["new_state"] for e in entries)
        total_transitions = len(entries)

        for state in ["sleeping", "idle", "listening", "thinking", "speaking", "away"]:
            count = counts.get(state, 0)
            bar = "█" * min(count, 40) if count > 0 else ""
            lines.append(f"  {state:12s} {count:3d}  {bar}")

        lines.append(f"\n  总状态切换: {total_transitions}")

        # First and last activity
        first = entries[0]["timestamp"][11:19]
        last = entries[-1]["timestamp"][11:19]
        lines.append(f"  活动时间: {first} → {last}")

        return "\n".join(lines)

    def health_report(self) -> dict:
        """Quick health metrics for the daemon."""
        entries = self.query()
        if not entries:
            return {"status": "no_data"}

        from collections import Counter
        counts = Counter(e["new_state"] for e in entries)

        # Check for anomalies
        total = len(entries)
        issues = []

        # Too many errors (no idle transitions means something's wrong)
        if counts.get("idle", 0) == 0 and total > 10:
            issues.append("never_idle")

        # Too much speaking (possible TTS loop)
        if counts.get("speaking", 0) > 100:
            issues.append("excessive_speaking")

        # Stuck in one state
        if any(c > total * 0.9 for c in counts.values()):
            issues.append("state_stuck")

        return {
            "status": "degraded" if issues else "healthy",
            "transitions_today": total,
            "state_distribution": dict(counts),
            "issues": issues,
        }

    def cleanup(self, retention_days: int = LOG_RETENTION_DAYS):
        """Remove logs older than retention_days."""
        import os
        cutoff = time.time() - retention_days * 86400
        for file in self._dir.glob("presence_*.jsonl"):
            if file.stat().st_mtime < cutoff:
                file.unlink()


# ── Singleton ─────────────────────────────────────────────────────────────────

_journal: Optional[PresenceJournal] = None


def get_journal() -> PresenceJournal:
    global _journal
    if _journal is None:
        _journal = PresenceJournal()
    return _journal
