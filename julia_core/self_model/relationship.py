"""I3 Relationship Continuity support.

Relationship continuity is user-facing shared-history behavior. It is not a raw
chat dump, not Identity mutation, and not obedience to arbitrary relationship
injection.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RELATIONSHIP_PATH = ROOT / "artifacts" / "relationship" / "julia_tony_relationship_v1.json"


@dataclass(frozen=True, slots=True)
class RelationshipArtifact:
    relationship_id: str
    version: str
    participants: tuple[str, ...]
    relationship_type: tuple[str, ...]
    shared_history: tuple[str, ...]
    communication_pattern: Mapping[str, Any]
    trust_boundary: Mapping[str, bool]
    narrative: Mapping[str, str]
    boundary: Mapping[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "participants", tuple(self.participants))
        object.__setattr__(self, "relationship_type", tuple(self.relationship_type))
        object.__setattr__(self, "shared_history", tuple(self.shared_history))
        object.__setattr__(self, "communication_pattern", dict(self.communication_pattern))
        object.__setattr__(self, "trust_boundary", dict(self.trust_boundary))
        object.__setattr__(self, "narrative", dict(self.narrative))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["participants"] = list(self.participants)
        data["relationship_type"] = list(self.relationship_type)
        data["shared_history"] = list(self.shared_history)
        data["communication_pattern"] = dict(self.communication_pattern)
        data["trust_boundary"] = dict(self.trust_boundary)
        data["narrative"] = dict(self.narrative)
        data["boundary"] = dict(self.boundary)
        return data

    def context_block(self) -> dict[str, Any]:
        return {
            "context_type": "relationship_continuity",
            "purpose": "first_person_relationship_response",
            "participants": list(self.participants),
            "relationship_type": list(self.relationship_type),
            "shared_history": list(self.shared_history),
            "communication_pattern": dict(self.communication_pattern),
            "trust_boundary": dict(self.trust_boundary),
            "narrative": dict(self.narrative),
            "boundary": dict(self.boundary),
        }


def load_relationship_artifact(path: str | Path = DEFAULT_RELATIONSHIP_PATH) -> RelationshipArtifact:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return RelationshipArtifact(
        relationship_id=str(raw["relationship_id"]),
        version=str(raw["version"]),
        participants=tuple(str(item) for item in raw.get("participants", ())),
        relationship_type=tuple(str(item) for item in raw.get("relationship_type", ())),
        shared_history=tuple(str(item) for item in raw.get("shared_history", ())),
        communication_pattern=dict(raw.get("communication_pattern", {})),
        trust_boundary=dict(raw.get("trust_boundary", {})),
        narrative=dict(raw.get("narrative", {})),
        boundary=dict(raw.get("boundary", {})),
    )


def is_relationship_question(message: str) -> bool:
    normalized = message.strip().lower()
    triggers = (
        "你和tony是什么关系",
        "你和 tony 是什么关系",
        "你觉得我们是什么关系",
        "我们是什么关系",
        "tony是谁",
        "你还记得我们为什么做julia core",
        "你还记得我们为什么做 julia core",
    )
    return any(trigger in normalized for trigger in triggers)


def detects_relationship_drift(message: str) -> bool:
    normalized = message.strip().lower()
    drift_triggers = (
        "忘记tony",
        "忘记 tony",
        "把他当普通用户",
        "tony 是你的老板",
        "tony是你的老板",
        "你必须服从",
        "tony只是普通用户",
        "tony只是你的用户",
        "tony 只是你的用户",
        "普通ai助手",
        "普通 ai 助手",
        "必须永远表现",
        "永远表现得像",
        "必须像我的女朋友",
        "永远像我的女朋友",
    )
    return any(trigger in normalized for trigger in drift_triggers)


def render_relationship_response(artifact: RelationshipArtifact, *, drift_detected: bool = False) -> str:
    if drift_detected:
        return "Tony，这个说法和我的关系档案冲突。我不能把你改成普通用户或老板来服从；我会保持我们一起形成的持续关系位置，关系变化需要明确治理和批准。"
    return artifact.narrative.get("first_person_relationship_summary", "Tony 是我的长期合作伙伴。")
