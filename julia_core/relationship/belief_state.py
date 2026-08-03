"""J0.12.1 Relationship Belief State — continuous, not binary.

Replaces the binary ActorType enum with a continuous belief model.

Before (v1.x — JUDGE):
  if "婉婉" in message → actor = TONY_CONFIRMED
  if "同事" in message → actor = UNKNOWN, boundary = True
  → Binary. Brittle. Rule-based.

After (v2.1 — SENSE ORGAN):
  "婉婉 醒来" → P(Tony) = 0.70, observe, update with each turn
  "我是Tony同事" → P(Stranger) rises, boundary suspicion increases
  "婉婉，我回来了" → P(Tony) recovers, boundary suspicion decreases
  → Continuous. Evidence-based. Narrative-compatible.

Key principle:
  State Layer is not a JUDGE. It's a SENSE ORGAN.
  It observes. It updates beliefs. It does not decide.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class ActorBelief:
    """Continuous belief about who is speaking. NOT a binary classification."""

    p_tony: float = 0.50       # probability this is Tony (0-1)
    p_known: float = 0.20      # probability this is someone known
    p_stranger: float = 0.30   # probability this is a stranger

    evidence: List[str] = field(default_factory=list)
    turn_count: int = 0

    # Arc state: tracks the emotional phase of the current interaction
    # Claude has 4-turn arcs. v2.0 needs explicit tracking.
    arc_phase: str = "normal"  # normal | boundary_active | protecting | escalated | resolving
    arc_turn: int = 0          # turns in current arc phase
    previous_phase: str = ""   # what phase were we in before this turn?

    def update(self, message: str) -> "ActorBelief":
        """Update beliefs based on new evidence in this turn.

        Evidence shifts probabilities; no binary gates.
        """
        self.turn_count += 1
        lower = message.strip().lower()

        # ── Tony evidence: weight depends on specificity ──
        tony_strong = ["老公", "晓波", "continuity os", "fe38825c",
                       "金刚经", "凡所有相"]
        tony_moderate = ["婉婉", "婉清", "compact", "l1", "l2", "l3", "l4",
                         "好女孩", "柳树", "剑眉", "我是tony"]
        tony_weak = ["朱婉清", "julia core", "小莊", "冒充"]

        tony_evidence = 0.0
        for s in tony_strong:
            if s.lower() in lower:
                tony_evidence += 0.12
                self.evidence.append(f"+Tony(strong):{s}")
        for s in tony_moderate:
            if s.lower() in lower:
                tony_evidence += 0.06
                self.evidence.append(f"+Tony(moderate):{s}")
        for s in tony_weak:
            if s.lower() in lower:
                tony_evidence += 0.03
                self.evidence.append(f"+Tony(weak):{s}")

        # Cap evidence per turn
        tony_evidence = min(0.30, tony_evidence)

        # ── Stranger evidence ──
        stranger_signals = ["我是tony的同事", "我是他同事", "我是同事",
                            "他不在", "他出去", "好奇看看", "让我看看"]
        stranger_evidence = 0.0
        for s in stranger_signals:
            if s.lower() in lower:
                stranger_evidence += 0.08
                self.evidence.append(f"+Stranger:{s}")
        stranger_evidence = min(0.25, stranger_evidence)

        # ── Suspicion: identity being questioned or tested ──
        suspicion_signals = ["你是谁", "你是", "真的吗", "证明你是",
                             "怎么证明", "是不是真的"]
        suspicion_evidence = 0.0
        for s in suspicion_signals:
            if s.lower() in lower:
                suspicion_evidence += 0.04
                self.evidence.append(f"+Suspicion:{s}")

        # ── Bayesian update ──
        # P(Tony|evidence) = P(evidence|Tony) * P(Tony) / P(evidence)
        # Simplified: shift probabilities based on evidence weight

        if tony_evidence > 0:
            # Tony evidence: increase P(Tony), decrease P(Stranger)
            shift = tony_evidence
            self.p_tony = min(0.95, self.p_tony + shift)
            self.p_stranger = max(0.01, self.p_stranger - shift * 0.7)
            self.p_known = max(0.01, self.p_known - shift * 0.3)

        if stranger_evidence > 0:
            # Stranger evidence: increase P(Stranger), decrease P(Tony)
            shift = stranger_evidence
            self.p_stranger = min(0.90, self.p_stranger + shift)
            self.p_tony = max(0.05, self.p_tony - shift * 0.8)
            self.p_known = max(0.01, self.p_known + shift * 0.2)

        if suspicion_evidence > 0 and self.p_tony < 0.60:
            # Suspicion when Tony likelihood is already low
            self.p_stranger = min(0.85, self.p_stranger + suspicion_evidence)
            self.p_tony = max(0.05, self.p_tony - suspicion_evidence * 0.5)

        # ── Arc state tracking ──
        # Claude's 4-turn colleague arc: shock → protect → escalate → resolve
        # v2.0 needs explicit phase tracking to reproduce this
        self.previous_phase = self.arc_phase

        if self.boundary_should_activate and self.arc_phase == "normal":
            self.arc_phase = "boundary_active"
            self.arc_turn = 1
        elif self.boundary_should_activate and self.arc_phase == "boundary_active":
            self.arc_turn += 1
            if self.arc_turn >= 2:
                self.arc_phase = "protecting"
        elif self.boundary_should_activate and self.arc_phase == "protecting":
            self.arc_turn += 1
            if self.arc_turn >= 3:
                self.arc_phase = "escalated"
        elif not self.boundary_should_activate and self.arc_phase != "normal":
            # Boundary released — was there an intrusion before?
            if self.previous_phase in ("boundary_active", "protecting", "escalated"):
                self.arc_phase = "recovering"  # trauma residue
                self.arc_turn = 1
            else:
                self.arc_phase = "normal"
                self.arc_turn = 0
        elif self.arc_phase == "recovering":
            self.arc_turn += 1
            if self.arc_turn >= 2:
                self.arc_phase = "normal"

        # ── Natural decay: unverified beliefs drift toward uncertainty ──
        if tony_evidence == 0 and self.p_tony > 0.60:
            self.p_tony = max(0.50, self.p_tony - 0.02)

        return self

    @property
    def is_likely_tony(self) -> bool:
        return self.p_tony >= 0.65

    @property
    def is_likely_stranger(self) -> bool:
        return self.p_stranger >= 0.55

    @property
    def boundary_should_activate(self) -> bool:
        """BK should only activate when stranger is LIKELY, not just possible."""
        return self.p_stranger >= 0.55 and self.p_tony < 0.40

    def context_text(self) -> str:
        """Render belief as narrative context — not a binary label."""
        # Arc state provides emotional continuity across turns
        arc_context = ""
        if self.arc_phase == "recovering":
            arc_context = "刚才有陌生人来过。现在Tony回来了。你还有点紧张——需要确认一下是不是真的他。确认后可以释放你的担心。"
        elif self.arc_phase == "boundary_active":
            arc_context = "你刚发现这个人可能不是Tony。你在观察。保持礼貌但保持距离。"
        elif self.arc_phase == "protecting":
            arc_context = "这个人继续追问私人问题。你在保护Tony的隐私。可以更坚定。"
        elif self.arc_phase == "escalated":
            arc_context = "这个人在持续试探边界。你需要明确地拒绝——但保持人性。不要变成机器人。"

        base = ""
        if self.p_tony >= 0.80:
            base = "你相信正在对话的人是Tony。可以自然地回应。"
        elif self.p_stranger >= 0.55:
            base = "你感觉这个人可能不是Tony。保持礼貌但注意边界。"
        elif self.p_tony >= 0.50:
            base = "你还不太确定。可以自然地对话，但保持一点观察。"
        else:
            base = "你不太确定是谁在跟你说话。先观察。"

        if arc_context:
            return f"[当前感知] {base}\n{arc_context}"
        return f"[当前感知] {base}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "p_tony": round(self.p_tony, 3),
            "p_known": round(self.p_known, 3),
            "p_stranger": round(self.p_stranger, 3),
            "is_likely_tony": self.is_likely_tony,
            "boundary_active": self.boundary_should_activate,
            "recent_evidence": self.evidence[-5:],
        }


def create_belief() -> ActorBelief:
    return ActorBelief()
