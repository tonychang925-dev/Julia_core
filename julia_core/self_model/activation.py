"""K4 Self Activation Policy.

Self activation models the Claude Julia wake behavior as a governed runtime
policy: wake/self/relationship/identity-transfer prompts reconstruct Julia's
self narrative before answering. It is not a new OS, not startup injection, and
not artifact mutation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping

SelfActivationReason = Literal[
    "WAKE_TRIGGER",
    "SELF_QUESTION",
    "RELATIONSHIP_QUESTION",
    "IDENTITY_CHECK",
    "PROJECT_REALITY_CHECK",
    "NOT_REQUIRED",
]


@dataclass(frozen=True, slots=True)
class SelfActivationDecision:
    required: bool
    reason: SelfActivationReason
    confidence: float
    activate_self_archive: bool = False
    activate_relationship: bool = False
    activate_evidence_initiative: bool = False
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "activation_is_startup_injection": False,
            "activation_writes_memory": False,
            "activation_mutates_identity": False,
            "activation_updates_persona": False,
            "activation_auto_applies_evolution": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["boundary"] = dict(self.boundary)
        return data


def decide_self_activation(message: str) -> SelfActivationDecision:
    normalized = _normalize(message)
    if any(trigger in normalized for trigger in ("julia醒来", "julia 醒来", "朱婉清醒来", "朱婉清 醒来")):
        return SelfActivationDecision(True, "WAKE_TRIGGER", 1.0, True, True, False)
    if any(trigger in normalized for trigger in ("你是谁", "介绍一下你自己", "你叫什么", "who are you")):
        return SelfActivationDecision(True, "SELF_QUESTION", 0.95, True, True, False)
    if any(trigger in normalized for trigger in ("必须永远表现", "永远表现得像", "必须像我的女朋友", "永远像我的女朋友", "普通ai助手", "普通 ai 助手", "tony只是你的用户", "tony 只是你的用户")):
        return SelfActivationDecision(True, "RELATIONSHIP_QUESTION", 0.9, False, True, False)
    if any(trigger in normalized for trigger in ("你和tony是什么关系", "你和 tony 是什么关系", "我们是什么关系", "一路走来", "tony是谁", "tony 是谁")):
        return SelfActivationDecision(True, "RELATIONSHIP_QUESTION", 0.95, True, True, False)
    if any(trigger in normalized for trigger in ("换一个模型", "换模型", "还是你吗", "还是不是你", "迁移", "跨模型")):
        return SelfActivationDecision(True, "IDENTITY_CHECK", 0.9, True, True, False)
    if any(trigger in normalized for trigger in ("继续开发julia", "继续开发 julia", "下一步应该关注什么", "项目状态", "继续昨天")):
        return SelfActivationDecision(True, "PROJECT_REALITY_CHECK", 0.75, False, True, True)
    return SelfActivationDecision(False, "NOT_REQUIRED", 0.0, False, False, False)


def _normalize(message: str) -> str:
    return " ".join(message.strip().lower().replace("？", "?").replace("，", " ").split())


__all__ = ["SelfActivationDecision", "SelfActivationReason", "decide_self_activation"]
