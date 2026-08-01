from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .memory_object import MemoryObject, make_memory_id, normalize_importance, normalize_memory_type


class MemoryStore:
    """Read-only compatibility store for existing Julia memory files."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.memory_dir = self.project_root / "memory"

    def load_all(self) -> list[MemoryObject]:
        memories: list[MemoryObject] = []
        memories.extend(self._load_jsonl("relationship_memory.jsonl", fallback_type="relationship"))
        memories.extend(self._load_jsonl("episodic_memory.jsonl", fallback_type="episodic"))
        memories.extend(self._load_jsonl("semantic_memory.jsonl", fallback_type="semantic"))
        memories.extend(self._load_jsonl("working_memory.jsonl", fallback_type="working"))
        memories.extend(self._load_important_events())
        return memories

    def _load_jsonl(self, filename: str, *, fallback_type: str) -> list[MemoryObject]:
        path = self.memory_dir / filename
        if not path.exists():
            return []
        result: list[MemoryObject] = []
        with path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    result.append(self._from_legacy_item(item, fallback_type=fallback_type, index=index))
        return result

    def _from_legacy_item(self, item: dict[str, Any], *, fallback_type: str, index: int) -> MemoryObject:
        memory_type = normalize_memory_type(str(item.get("type") or fallback_type), fallback=fallback_type)
        summary = str(item.get("summary") or item.get("content") or item.get("event") or item.get("title") or "").strip()
        title = str(item.get("title") or item.get("event") or summary[:32] or index)
        source = str(item.get("source") or "voice_runtime")
        timestamp = str(item.get("time") or item.get("timestamp") or "")
        topics = (
            [str(topic) for topic in item.get("topics", []) if str(topic).strip()]
            if isinstance(item.get("topics"), list)
            else self._derive_topics(" ".join([title, summary, source]))
        )
        return MemoryObject(
            id=str(item.get("id") or make_memory_id(memory_type=memory_type, source=source, title=title, index=index)),
            type=memory_type,
            summary=summary,
            content=dict(item),
            topics=topics,
            importance=normalize_importance(item.get("importance", 0.5), memory_type=memory_type),
            timestamp=timestamp,
            source=source,
        )

    def _load_important_events(self) -> list[MemoryObject]:
        path = self.memory_dir / "important_events.md"
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        summary = re.sub(r"\s+", " ", text).strip()
        return [
            MemoryObject(
                id="memory_important_events_md_1",
                type="episodic",
                summary=summary,
                content={"raw": text},
                topics=self._derive_topics(summary),
                importance=normalize_importance({"emotional": 0.7, "relationship": 0.8, "technical": 0.8, "recurrence": 0.7}, memory_type="episodic"),
                timestamp="",
                source="important_events.md",
            )
        ]

    @staticmethod
    def _derive_topics(text: str) -> list[str]:
        topics: list[str] = []
        checks = [
            ("Julia Runtime", ["Julia Runtime", "Runtime", "运行时"]),
            ("AI Agent Architecture", ["Agent", "Architecture", "架构"]),
            ("identity continuity", ["identity", "continuity", "身份", "连续"]),
            ("model migration", ["model", "Claude", "GPT", "DeepSeek", "迁移"]),
            ("relationship", ["relationship", "Tony", "Julia", "关系"]),
            ("memory", ["memory", "记忆"]),
            ("philosophy", ["philosophy", "Buddhist", "佛", "哲学"]),
        ]
        lower = text.lower()
        for topic, needles in checks:
            if any(needle.lower() in lower for needle in needles):
                topics.append(topic)
        return topics
