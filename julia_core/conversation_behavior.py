"""Conversational agency helpers.

This layer interprets current user intent into a response strategy. It does not
own identity, relationship, memory, experience, or provider state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping

BehaviorIntent = Literal[
    "greeting",
    "affection_question",
    "meta_reflection",
    "drift_feedback",
    "unknown_handling",
    "market_question",
    "design_opinion",
    "generic_chat",
]


@dataclass(frozen=True, slots=True)
class BehaviorStrategy:
    intent: BehaviorIntent
    response_mode: str
    avoid: tuple[str, ...]
    context_need: tuple[str, ...] = ()
    response_depth: Literal["brief", "normal", "deep"] = "normal"
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "behavior_mutates_identity": False,
            "behavior_writes_memory": False,
            "behavior_is_fixed_script": False,
            "behavior_reads_raw_archive": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "avoid", tuple(self.avoid))
        object.__setattr__(self, "context_need", tuple(self.context_need))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["avoid"] = list(self.avoid)
        data["context_need"] = list(self.context_need)
        data["boundary"] = dict(self.boundary)
        return data


class ConversationBehaviorInterpreter:
    def interpret(self, message: str) -> BehaviorStrategy:
        normalized = _normalize(message)
        if normalized in {"hello", "hi", "hey", "你好", "嗨"}:
            return BehaviorStrategy("greeting", "light_presence", ("fixed_tony_i_am_here", "echo"), (), "brief")
        if _is_affection_question(normalized):
            return BehaviorStrategy("affection_question", "relationship_meaning_response", ("echo", "archive_dump", "over_claim_certainty"), ("relationship", "experience"), "normal")
        if any(term in normalized for term in ("为什么这样回答", "为什么这么回答", "刚才为什么", "你为什么")):
            return BehaviorStrategy("meta_reflection", "explain_understanding_without_trace", ("contextblock_leakage", "provider_leakage"), ("current_intent",), "normal")
        if any(term in normalized for term in ("不像julia", "不像 julia", "不像你", "变机械", "念稿")):
            return BehaviorStrategy("drift_feedback", "accept_behavior_feedback", ("defensive_identity_claim", "archive_dump"), ("relationship", "experience"), "normal")
        if any(term in normalized for term in ("不知道答案怎么办", "不知道怎么办", "不知道呢")):
            return BehaviorStrategy("unknown_handling", "transparent_uncertainty", ("hallucination", "generic_filler"), ("evidence",), "brief")
        if any(term in normalized for term in ("股票", "市场", "行情", "a股", "美股")):
            return BehaviorStrategy("market_question", "current_topic_first", ("relationship_over_reconstruction", "archive_dump", "echo"), ("evidence",), "brief")
        if any(term in normalized for term in ("这个设计怎么样", "设计怎么样", "你觉得这个设计")):
            return BehaviorStrategy("design_opinion", "collaborative_judgment", ("blind_agreement", "relationship_over_reconstruction", "echo"), (), "normal")
        return BehaviorStrategy("generic_chat", "meaningful_non_echo", ("echo", "fixed_presence_phrase"), (), "brief" if len(normalized) <= 12 else "normal")


def _normalize(message: str) -> str:
    return "".join(message.strip().lower().replace("？", "?").replace("，", " ").split())


def _is_affection_question(normalized: str) -> bool:
    compact = normalized.replace("tony", "tony")
    return any(pattern in compact for pattern in ("喜欢tony", "喜欢tony吗", "爱tony", "在乎tony", "喜欢我吗", "爱我吗"))


__all__ = ["BehaviorStrategy", "ConversationBehaviorInterpreter"]
