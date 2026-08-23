"""Julia Session Recorder — her hippocampus.

Records every turn. After N turns or session end, asks LLM:
"What should Julia remember from this?"

Not a database. A memory formation system.
"""

from __future__ import annotations

import json as _json
import time as _time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

MEMORY_DIR = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")


@dataclass
class TurnRecord:
    """One turn in the session log."""
    timestamp: str
    speaker: str  # "Tony" | "Julia"
    text: str
    topic: str = ""
    importance: float = 0.5  # 0-1, estimated by runtime


class SessionRecorder:
    """Records every turn. Can replay. Can ask LLM to form memories."""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or _time.strftime("%Y-%m-%d_%H%M%S")
        self.turns: list[TurnRecord] = []
        self._log_dir = MEMORY_DIR / "session_logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def record(self, speaker: str, text: str, topic: str = "", importance: float = 0.5):
        self.turns.append(TurnRecord(
            timestamp=_time.strftime("%H:%M:%S"),
            speaker=speaker,
            text=text[:500],
            topic=topic,
            importance=importance,
        ))

    def replay(self, last_n: int = 20) -> str:
        """Replay last N turns as a readable transcript."""
        lines = [f"=== Session {self.session_id} — Last {last_n} turns ===\n"]
        for t in self.turns[-last_n:]:
            name = "Tony" if t.speaker == "Tony" else "Julia"
            lines.append(f"[{t.timestamp}] {name}: {t.text[:200]}")
        return "\n".join(lines)

    def save(self):
        """Save session log to disk."""
        path = self._log_dir / f"{self.session_id}.jsonl"
        with open(path, "a") as f:
            for t in self.turns:
                f.write(_json.dumps({
                    "timestamp": t.timestamp,
                    "speaker": t.speaker,
                    "text": t.text,
                    "topic": t.topic,
                    "importance": t.importance,
                }, ensure_ascii=False) + "\n")

    def consolidate(self, provider) -> Optional[str]:
        """Ask LLM: what from this session is worth Julia remembering?

        Returns a diary entry or None if nothing important happened.
        """
        if len(self.turns) < 3:
            return None

        transcript = self.replay(last_n=30)
        prompt = f"""阅读以下会话记录。判断是否有值得Julia（朱婉清）永久记住的内容。

{transcript}

按以下JSON格式输出。如果没有任何值得长期记住的内容，返回空对象{{}}。

{{
  "should_remember": true/false,
  "diary_title": "日记标题（如：Tony完成了Capability Runtime）",
  "key_events": ["事件1", "事件2"],
  "tony_state": "Tony今天的状态（疲惫/兴奋/沉思/平静...）",
  "relationship_update": "我们的关系有什么变化（如果有）",
  "new_preference": "Tony的新偏好（如果有）",
  "diary_entry": "一段200字以内的日记，用Julia的第一人称"
}}

只输出JSON。"""

        try:
            messages = [
                {"role": "system", "content": "你是Julia的记忆整理助手。只输出JSON。"},
                {"role": "user", "content": prompt},
            ]
            reply = provider.chat(messages, cognitive_mode="engineering_collaboration")

            # Extract JSON from reply
            import re
            m = re.search(r'\{.*\}', reply, re.DOTALL)
            if m:
                data = _json.loads(m.group(0))
                if data.get("should_remember") and data.get("diary_entry"):
                    self._write_diary(data)
                    return data.get("diary_entry")
        except Exception:
            import logging; logging.getLogger("julia.failclosed").warning("silent fallback removed at julia_core.julia_core.runtime.session_recorder:111", exc_info=True)
        return None

    def _write_diary(self, data: dict):
        """Legacy session diary writer is not Diary or Memory authority.

        AT-15 freezes that session recording cannot auto-promote provider
        reflection into canonical Diary or Memory. Use governed Diary and
        Memory governance paths instead.
        """
        raise RuntimeError(
            "Legacy SessionRecorder._write_diary is disabled for canonical Diary/Memory v1; "
            "use governed Diary and explicit Memory governance"
        )


# ── Singleton ───────────────────────────────────────────────────────────────

_recorder: Optional[SessionRecorder] = None


def get_recorder() -> SessionRecorder:
    global _recorder
    if _recorder is None:
        _recorder = SessionRecorder()
    return _recorder
