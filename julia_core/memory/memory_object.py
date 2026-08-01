from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MEMORY_TYPES = {"episodic", "semantic", "relationship", "working"}
IMPORTANCE_KEYS = ("emotional", "relationship", "technical", "recurrence")


@dataclass(frozen=True)
class MemoryObject:
    id: str
    type: str
    summary: str
    content: dict[str, object]
    topics: list[str]
    importance: dict[str, float]
    timestamp: str
    source: str


def normalize_importance(value: Any, *, memory_type: str = "semantic") -> dict[str, float]:
    if isinstance(value, dict):
        result = {key: _clamp(value.get(key, 0.0)) for key in IMPORTANCE_KEYS}
    else:
        scalar = _clamp(value if isinstance(value, (int, float)) else 0.5)
        result = {key: scalar for key in IMPORTANCE_KEYS}
    if memory_type == "relationship":
        result["relationship"] = max(result["relationship"], 0.75)
        result["emotional"] = max(result["emotional"], 0.5)
    elif memory_type == "episodic":
        result["recurrence"] = max(result["recurrence"], 0.4)
    elif memory_type == "semantic":
        result["technical"] = max(result["technical"], 0.5)
    return result


def normalize_memory_type(raw_type: str, *, fallback: str = "semantic") -> str:
    value = (raw_type or "").strip()
    relationship_aliases = {
        "relationship",
        "user_profile",
        "shared_memory",
        "relationship_contract",
        "shared_diary",
        "communication_preference",
    }
    if value in relationship_aliases:
        return "relationship"
    if value in MEMORY_TYPES:
        return value
    return fallback if fallback in MEMORY_TYPES else "semantic"


def make_memory_id(*, memory_type: str, source: str, title: str, index: int) -> str:
    raw = f"{memory_type}_{source}_{title}_{index}"
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", raw).strip("_") or str(index)
    return f"memory_{slug[:96]}"


def _clamp(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return max(0.0, min(1.0, number))
