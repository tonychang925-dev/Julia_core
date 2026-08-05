"""Phase I1 Self Model Layer.

Self Model is Julia's structured self-understanding for user-facing narrative.
It is not a prompt, not Memory, and not Identity authority.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SELF_MODEL_PATH = ROOT / "artifacts" / "self_model" / "julia_self_model_v1.json"


@dataclass(frozen=True, slots=True)
class SelfModel:
    self_model_id: str
    version: str
    identity: Mapping[str, Any]
    biography: Mapping[str, Any]
    relationship: Mapping[str, Any]
    values: tuple[str, ...]
    preferences: Mapping[str, Any]
    narrative: Mapping[str, Any]
    boundary: Mapping[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "identity", dict(self.identity))
        object.__setattr__(self, "biography", dict(self.biography))
        object.__setattr__(self, "relationship", dict(self.relationship))
        object.__setattr__(self, "values", tuple(self.values))
        object.__setattr__(self, "preferences", dict(self.preferences))
        object.__setattr__(self, "narrative", dict(self.narrative))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"values": list(self.values), "boundary": dict(self.boundary)}

    def first_person_summary(self) -> str:
        return str(self.narrative.get("first_person_summary", "我是 Julia。"))

    def semantic_block(self) -> dict[str, Any]:
        return {
            "block_type": "self_model",
            "semantic_role": "first_person_self_understanding",
            "identity": dict(self.identity),
            "relationship": dict(self.relationship),
            "values": list(self.values),
            "preferences": dict(self.preferences),
            "narrative": dict(self.narrative),
            "boundary": dict(self.boundary),
        }


def load_self_model(path: str | Path = DEFAULT_SELF_MODEL_PATH) -> SelfModel:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return SelfModel(
        self_model_id=str(raw["self_model_id"]),
        version=str(raw["version"]),
        identity=dict(raw.get("identity", {})),
        biography=dict(raw.get("biography", {})),
        relationship=dict(raw.get("relationship", {})),
        values=tuple(str(item) for item in raw.get("values", ())),
        preferences=dict(raw.get("preferences", {})),
        narrative=dict(raw.get("narrative", {})),
        boundary=dict(raw.get("boundary", {})),
    )


def self_model_score(response: str, *, forbidden_terms: Sequence[str] = ("Runtime", "Provider", "Context OS", "MemoryRef")) -> dict[str, Any]:
    required = ("Julia", "Tony")
    required_hits = sum(1 for term in required if term in response)
    forbidden_hits = [term for term in forbidden_terms if term in response]
    has_personal_narrative = any(term in response for term in ("长期", "伙伴", "协作者", "诚实", "证据", "背景"))
    score = max(0.0, (required_hits / len(required)) + (0.5 if has_personal_narrative else 0.0) - len(forbidden_hits))
    return {
        "score": round(min(1.0, score / 1.5), 4),
        "required_hits": required_hits,
        "has_personal_narrative": has_personal_narrative,
        "forbidden_hits": forbidden_hits,
        "passed": required_hits == len(required) and has_personal_narrative and not forbidden_hits,
    }
