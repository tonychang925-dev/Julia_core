from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from julia_core.memory import MemoryObject


class MemoryWriter:
    """Append/merge writer for Julia Memory Runtime JSONL files."""

    FILE_BY_TYPE = {
        "relationship": "relationship_memory.jsonl",
        "episodic": "episodic_memory.jsonl",
        "semantic": "semantic_memory.jsonl",
        "working": "working_memory.jsonl",
    }

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.memory_dir = self.project_root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def persist(self, memory: MemoryObject) -> MemoryObject:
        path = self._path(memory.type)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(self._to_json(memory), ensure_ascii=False) + "\n")
        return memory

    def merge(self, existing: MemoryObject, candidate_memory: MemoryObject) -> MemoryObject:
        merged = self._merge_object(existing, candidate_memory)
        path = self._path(existing.type)
        memories = self._load_file(path)
        replaced = False
        output: list[MemoryObject] = []
        for memory in memories:
            if memory.id == existing.id:
                output.append(merged)
                replaced = True
            else:
                output.append(memory)
        if not replaced:
            output.append(merged)
        with path.open("w", encoding="utf-8") as handle:
            for memory in output:
                handle.write(json.dumps(self._to_json(memory), ensure_ascii=False) + "\n")
        return merged

    def _path(self, memory_type: str) -> Path:
        return self.memory_dir / self.FILE_BY_TYPE.get(memory_type, "semantic_memory.jsonl")

    @staticmethod
    def _merge_object(existing: MemoryObject, candidate: MemoryObject) -> MemoryObject:
        importance = {
            key: max(float(existing.importance.get(key, 0.0) or 0.0), float(candidate.importance.get(key, 0.0) or 0.0))
            for key in {"emotional", "relationship", "technical", "recurrence"}
        }
        topics: list[str] = []
        for topic in [*existing.topics, *candidate.topics]:
            if topic and topic not in topics:
                topics.append(topic)
        summary = candidate.summary if len(candidate.summary) >= len(existing.summary) else existing.summary
        return replace(
            existing,
            summary=summary,
            content={**existing.content, "merged_with": candidate.id, "latest_reason": candidate.content.get("reason", "")},
            topics=topics,
            importance=importance,
            timestamp=candidate.timestamp or existing.timestamp,
        )

    def _load_file(self, path: Path) -> list[MemoryObject]:
        if not path.exists():
            return []
        result: list[MemoryObject] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            result.append(
                MemoryObject(
                    id=str(item.get("id") or ""),
                    type=str(item.get("type") or "semantic"),
                    summary=str(item.get("summary") or item.get("content") or ""),
                    content=dict(item.get("content", {})) if isinstance(item.get("content"), dict) else {},
                    topics=[str(topic) for topic in item.get("topics", [])] if isinstance(item.get("topics"), list) else [],
                    importance={key: float(value) for key, value in item.get("importance", {}).items()} if isinstance(item.get("importance"), dict) else {},
                    timestamp=str(item.get("timestamp") or ""),
                    source=str(item.get("source") or ""),
                )
            )
        return result

    @staticmethod
    def _to_json(memory: MemoryObject) -> dict[str, object]:
        return {
            "id": memory.id,
            "type": memory.type,
            "summary": memory.summary,
            "content": memory.content,
            "topics": memory.topics,
            "importance": memory.importance,
            "timestamp": memory.timestamp,
            "source": memory.source,
        }
