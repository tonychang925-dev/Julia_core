"""I2 Self Archive Recall Runtime.

This module retrieves private persona archive facts on demand and reconstructs a
semantic self narrative block. It is not startup injection, not a memory reference, and
not raw prompt dumping.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRIVATE_IDENTITY_FACTS = ROOT.parent / "julia_agent" / "memory" / "governed" / "identity_facts.json"
SelfRecallRequestType = Literal["self_identity_question", "self_profile_recall", "self_biography_question", "not_self_related"]


@dataclass(frozen=True, slots=True)
class PersonaArchiveRef:
    archive_ref: str
    type: str
    authority: str
    path: str
    exists: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SelfRecallDecision:
    request_type: SelfRecallRequestType
    recall_required: bool
    sources: tuple[str, ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "sources", tuple(self.sources))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["sources"] = list(self.sources)
        return data


@dataclass(frozen=True, slots=True)
class SelfNarrativeContextBlock:
    context_type: str
    purpose: str
    grounding: tuple[str, ...]
    archive_refs: tuple[PersonaArchiveRef, ...]
    facts: Mapping[str, str]
    conflicts: tuple[str, ...] = ()
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "block_is_memory_ref": False,
            "block_is_raw_archive_dump": False,
            "block_mutates_identity": False,
            "block_updates_self_model": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "grounding", tuple(self.grounding))
        object.__setattr__(self, "archive_refs", tuple(self.archive_refs))
        object.__setattr__(self, "facts", dict(self.facts))
        object.__setattr__(self, "conflicts", tuple(self.conflicts))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_type": self.context_type,
            "purpose": self.purpose,
            "grounding": list(self.grounding),
            "archive_refs": [ref.to_dict() for ref in self.archive_refs],
            "facts": dict(self.facts),
            "conflicts": list(self.conflicts),
            "boundary": dict(self.boundary),
        }


def decide_self_recall(message: str) -> SelfRecallDecision:
    normalized = message.strip().lower()
    profile_triggers = ("读一下你的档案", "读取你的档案", "看一下你的档案", "看看你的档案", "你的档案", "read your profile", "load your profile")
    biography_triggers = ("你的背景", "介绍一下你的背景", "你的家庭", "你爸爸", "你妈妈", "你是做什么", "你的工作", "哪个大学", "什么专业")
    identity_triggers = ("你是谁", "介绍一下你自己", "who are you")
    if any(trigger in normalized for trigger in profile_triggers):
        return SelfRecallDecision("self_profile_recall", True, ("persona_archive",), "explicit_profile_archive_request")
    if any(trigger in normalized for trigger in biography_triggers):
        return SelfRecallDecision("self_biography_question", True, ("persona_archive",), "biography_or_family_question")
    if any(trigger in normalized for trigger in identity_triggers):
        return SelfRecallDecision("self_identity_question", True, ("self_model", "persona_archive"), "self_identity_question")
    return SelfRecallDecision("not_self_related", False, (), "no_self_recall_trigger")


class SelfArchiveRetriever:
    def __init__(self, identity_facts_path: str | Path = DEFAULT_PRIVATE_IDENTITY_FACTS) -> None:
        self.identity_facts_path = Path(identity_facts_path)

    def retrieve(self, decision: SelfRecallDecision) -> SelfNarrativeContextBlock | None:
        if not decision.recall_required:
            return None
        ref = PersonaArchiveRef(
            archive_ref="persona://private/julia-governed-identity-facts-v1",
            type="biography",
            authority="private_persona_archive",
            path=str(self.identity_facts_path),
            exists=self.identity_facts_path.exists(),
        )
        if not ref.exists:
            return SelfNarrativeContextBlock(
                context_type="self_narrative",
                purpose="first_person_identity_response",
                grounding=("missing_persona_archive",),
                archive_refs=(ref,),
                facts={},
            )
        raw = json.loads(self.identity_facts_path.read_text(encoding="utf-8"))
        return SelfNarrativeContextBlock(
            context_type="self_narrative",
            purpose="first_person_identity_response",
            grounding=("biography", "relationship"),
            archive_refs=(ref,),
            facts=_flatten_identity_facts(raw),
            conflicts=_conflicts(raw),
        )


def _flatten_identity_facts(raw: Mapping[str, Any]) -> dict[str, str]:
    facts = dict(raw.get("facts", {}))

    def value(section: str, field: str) -> str:
        item = dict(dict(facts.get(section, {})).get(field, {}))
        return str(item.get("value", "")).strip()

    flattened = {
        "name": value("identity", "name"),
        "real_name": value("identity", "real_name"),
        "age": value("identity", "age"),
        "from": value("identity", "from"),
        "university": value("education", "university"),
        "major": value("education", "major"),
        "current_work": value("career", "current_work"),
        "father": value("family", "father"),
        "mother": value("family", "mother"),
        "brother": value("family", "brother"),
        "sibling_negative": value("family", "sibling_negative"),
        "tony": value("relationship", "tony"),
    }
    return {key: val for key, val in flattened.items() if val}


def _conflicts(raw: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(item.get("value", "")) for item in raw.get("negative_facts", ()) if item.get("value"))


def render_self_narrative(block: SelfNarrativeContextBlock | None) -> str:
    if block is None:
        return "Tony，我需要先确认自己的档案再回答。"
    if not block.facts:
        return "Tony，我没有找到这部分档案，所以我不想假设或编造。你可以让我继续搜索 workspace。"
    f = dict(block.facts)
    parts = [
        f"我是 {f.get('name', 'Julia')}，中文名叫{f.get('real_name', '朱婉清')}。",
        f"我来自{f.get('from', '档案未注明')}。",
    ]
    if f.get("current_work"):
        parts.append(f"现在{f['current_work']}。")
    if f.get("university") or f.get("major"):
        parts.append(f"我读的是{f.get('university', '')}{f.get('major', '')}。")
    family = [f.get("father", ""), f.get("mother", ""), f.get("brother", "")]
    family = [item for item in family if item]
    if family:
        parts.append("家里的情况是：" + "；".join(family) + "。")
    if f.get("tony"):
        parts.append(f.get("tony", ""))
    return "".join(parts)
