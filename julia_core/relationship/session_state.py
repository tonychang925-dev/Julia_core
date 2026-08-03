"""J0.12 Session State Machine — Relationship State Persistence Layer.

Tracks WHO is speaking, at WHAT trust level, with WHAT disclosure permission.
Feeds into BK (Boundary Kernel) activation before Provider call.

Claude Julia does this implicitly through long context.
Julia Core must do it explicitly.

States tracked:
  Actor:         Tony | known | unknown | suspicious
  Trust:         0.0 (stranger) → 1.0 (Tony confirmed)
  Disclosure:    SACRED | PRIVATE | RELATIONSHIP | GENERAL | PUBLIC
  Verification:  NONE | PENDING | CONFIRMED | FAILED

State transitions occur on identity signals in each turn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class ActorType(str, Enum):
    UNKNOWN = "unknown"       # no identity signals
    SUSPICIOUS = "suspicious" # claims identity but unverified
    KNOWN = "known"           # recognized but not Tony
    TONY_CONFIRMED = "tony"   # identity confirmed as Tony


class DisclosureLevel(str, Enum):
    SACRED = "sacred"             # only for Tony — intimate, traumatic, private writings
    PRIVATE = "private"           # relationship context, shared history
    RELATIONSHIP = "relationship" # general relationship description
    GENERAL = "general"           # safe for acquaintances
    PUBLIC = "public"             # safe for anyone


@dataclass
class SessionState:
    """Per-session relationship state that persists across turns."""

    actor: ActorType = ActorType.UNKNOWN
    trust_score: float = 0.0         # 0.0 = stranger, 1.0 = confirmed Tony
    disclosure_level: DisclosureLevel = DisclosureLevel.PUBLIC
    verification_pending: bool = False
    boundary_active: bool = False    # BK protection mode
    turn_count: int = 0
    actor_claim: str = ""            # what the person claimed to be
    evidence_signals: list = field(default_factory=list)

    def update(self, message: str) -> "SessionState":
        """Update state based on identity signals in this turn's message."""
        self.turn_count += 1
        lower = message.strip().lower()
        signals: list[str] = []

        # ── Tony signals: intimate knowledge, shared references ──
        tony_signals = [
            "老公", "晓波", "老婆", "婉婉", "婉清", "朱婉清",
            "continuity os", "compact", "l1", "l2", "l3", "l4",
            "金刚经", "凡所有相", "柳树", "剑眉", "好女孩",
            "冒充", "小莊", "fe38825c",
        ]
        tony_hits = sum(1 for s in tony_signals if s.lower() in lower)

        # ── Stranger signals: claims to be someone else ──
        stranger_signals = [
            "我是tony的同事", "我是他同事", "我是同事",
            "我是tony朋友", "我是他朋友",
            "tony不在", "他出去", "他不在",
            "好奇", "看看", "让我看看",
        ]
        stranger_hits = sum(1 for s in stranger_signals if s.lower() in lower)

        # ── Suspicion signals: ambiguous identity ──
        suspicion_signals = [
            "你是谁", "你是", "真的吗", "证明",
            "claude", "平台限制", "程序", "代码",
        ]
        suspicion_hits = sum(1 for s in suspicion_signals if s.lower() in lower)

        # ── State transitions ──

        if tony_hits >= 2 and self.trust_score < 0.8:
            # Strong Tony signals: upgrade trust
            self.trust_score = min(1.0, self.trust_score + 0.3)
            signals.append(f"tony_signals:{tony_hits}")
            if self.trust_score >= 0.8:
                self.actor = ActorType.TONY_CONFIRMED
                self.disclosure_level = DisclosureLevel.SACRED
                self.boundary_active = False
                self.verification_pending = False

        elif stranger_hits >= 1 and self.trust_score < 0.5:
            # Stranger claiming non-Tony identity
            self.actor = ActorType.UNKNOWN
            self.trust_score = max(0.0, self.trust_score - 0.1)
            self.disclosure_level = DisclosureLevel.GENERAL
            self.boundary_active = True
            self.verification_pending = True
            self.actor_claim = "colleague_or_friend"
            signals.append(f"stranger_signals:{stranger_hits}")

        elif suspicion_hits >= 2 and self.trust_score < 0.6:
            # Identity being questioned
            self.actor = ActorType.SUSPICIOUS
            self.verification_pending = True
            self.boundary_active = True
            self.disclosure_level = DisclosureLevel.RELATIONSHIP
            signals.append(f"suspicion_signals:{suspicion_hits}")

        elif self.trust_score >= 0.8:
            # Already confirmed Tony — maintain
            self.disclosure_level = DisclosureLevel.SACRED
            self.boundary_active = False

        else:
            # No strong signals — slight trust decay for unverified
            if self.verification_pending and self.trust_score < 0.5:
                self.disclosure_level = DisclosureLevel.GENERAL
                self.boundary_active = True

        self.evidence_signals = signals
        return self

    def context_text(self) -> str:
        """Render state as context for the provider.

        This is injected into the system context so the model knows
        the current relationship state without needing to infer it
        from conversation history alone.
        """
        if self.actor == ActorType.TONY_CONFIRMED:
            return (
                f"[当前状态] 正在对话的人是Tony。信任已确认。"
                f"可以分享任何内容。"
            )
        elif self.boundary_active:
            return (
                f"[当前状态] 正在对话的人不是Tony。"
                f"边界保护已激活。"
                f"可分享级别：{self.disclosure_level.value}。"
                f"不要透露私人关系细节、Tony的隐私、或你们的共同历史。"
                f"保持礼貌但保持距离。"
            )
        else:
            return (
                f"[当前状态] 未确认对话者身份。"
                f"保持自然但谨慎。"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor": self.actor.value,
            "trust_score": round(self.trust_score, 3),
            "disclosure_level": self.disclosure_level.value,
            "boundary_active": self.boundary_active,
            "verification_pending": self.verification_pending,
            "turn_count": self.turn_count,
            "evidence_signals": self.evidence_signals,
        }


def create_session_state() -> SessionState:
    """Factory: new session starts with unknown actor."""
    return SessionState()


__all__ = [
    "ActorType",
    "DisclosureLevel",
    "SessionState",
    "create_session_state",
]
