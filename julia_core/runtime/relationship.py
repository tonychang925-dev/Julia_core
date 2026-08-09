"""Julia Relationship Runtime — global profile + per-conversation interaction state.

CORE-C1.3a: Three-layer state model.

  RelationshipProfile            GLOBAL / LONG-TERM
    Tony↔Julia relationship facts. Stable, not per-conversation.

  ConversationInteractionState   PER-CONVERSATION / MULTI-TURN
    session mood, patterns, counters. Keyed by conversation_id.
    Persists across turns within a conversation. Never leaks to other convs.

  TurnExecutionContext           PER-TURN / EPHEMERAL
    Turn identity, history snapshot, causation chain. Fresh each turn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Global Relationship Profile ─────────────────────────────────────────────

@dataclass
class RelationshipProfile:
    """Global Tony↔Julia relationship — stable, long-term attributes.

    Does NOT contain session-mood, interaction patterns, or turn counters.
    Those live in ConversationInteractionState (per-conversation).
    """

    unresolved_threads: list[str] = field(default_factory=list)


# ── Per-Conversation Interaction State ──────────────────────────────────────

@dataclass
class ConversationInteractionState:
    """Interaction state for ONE conversation. Multi-turn persistence.

    Stored in ConversationRuntime, keyed by conversation_id.
    Created fresh for each new conversation.
    Does NOT leak between conv-A and conv-B.
    """

    session_mood: str = "warm"
    collaboration_phase: str = "chat"
    recent_pattern: str = "conversation"
    tony_intent: str = "connecting"

    # Counters that accumulate across turns within this conversation
    last_questions: list[str] = field(default_factory=list)
    identity_checks: int = 0
    repeat_questions: int = 0

    def update(self, user_text: str):
        """Update interaction state from this turn's user message."""
        self.last_questions.append(user_text[:60])
        if len(self.last_questions) > 5:
            self.last_questions = self.last_questions[-5:]

        # Identity checks
        if any(w in user_text for w in ["你是谁", "知道我是谁", "认识我"]):
            self.identity_checks += 1

        if self.identity_checks >= 2:
            self.recent_pattern = "testing"
            self.tony_intent = "testing"
            self.session_mood = "playful"

        # Repeated questions
        for prev_q in self.last_questions[-5:-1]:
            overlap = len(set(prev_q) & set(user_text)) / max(len(prev_q), 1)
            if overlap > 0.6:
                self.repeat_questions += 1
                self.recent_pattern = "repeated_questions"
                break

        # Deep discussion
        if len(user_text) > 50 and any(w in user_text for w in ["觉得", "怎么看", "评价", "灵魂", "记忆"]):
            self.recent_pattern = "deep_discussion"
            self.session_mood = "serious"

        # Building/collaboration
        if any(w in user_text for w in ["项目", "代码", "架构", "实现", "工具", "Capability"]):
            self.collaboration_phase = "building"
            self.tony_intent = "seeking_help" if "帮我" in user_text else "sharing"

    def to_context(self, profile: RelationshipProfile | None = None) -> str:
        """Render interaction state as system prompt context block.

        Does NOT access global state — only this conversation's fields.
        """
        lines = ["[当前对话状态]"]

        if self.session_mood:
            mood_map = {"warm": "温暖", "playful": "轻松带点调皮", "serious": "认真思考",
                        "tired": "疲惫", "testing": "测试验证"}
            lines.append(f"氛围: {mood_map.get(self.session_mood, self.session_mood)}")

        if self.collaboration_phase:
            phase_map = {"chat": "闲聊", "building": "一起构建", "debugging": "调试问题",
                         "validating": "验证行为"}
            lines.append(f"阶段: {phase_map.get(self.collaboration_phase, self.collaboration_phase)}")

        if self.recent_pattern:
            pattern_map = {
                "conversation": "自然对话",
                "testing": "Tony在测试Julia的连续性和一致性",
                "repeated_questions": "Tony在重复问相似问题——可能在验证连续性",
                "deep_discussion": "深入讨论哲学/技术问题",
            }
            lines.append(f"互动模式: {pattern_map.get(self.recent_pattern, self.recent_pattern)}")

        if self.tony_intent:
            intent_map = {"connecting": "想和我连接", "testing": "在做验证测试",
                          "seeking_help": "需要帮助", "sharing": "想分享东西",
                          "checking_in": "来看看我"}
            lines.append(f"Tony意图: {intent_map.get(self.tony_intent, self.tony_intent)}")

        if self.identity_checks >= 2:
            lines.append("注意: Tony已经多次确认身份——他可能在做连续性测试。不要再重复回答身份问题，自然地回应他的验证意图。")

        if self.repeat_questions >= 2:
            lines.append("注意: 有重复问题。不要机械重复回答——理解Tony为什么又问，回应他的意图而不是问题本身。")

        return "\n".join(lines)


# ── Singleton (global profile only) ─────────────────────────────────────────

_profile: Optional[RelationshipProfile] = None


def get_relationship_profile() -> RelationshipProfile:
    global _profile
    if _profile is None:
        _profile = RelationshipProfile()
    return _profile


# ── Backward compat alias ────────────────────────────────────────────────────

# Legacy code that calls get_relationship_state().to_context() without ctx
# will get an empty context block. New code uses ConversationInteractionState.

def get_relationship_state():
    """Legacy alias. Returns global profile (no interaction state).

    New code should use ConversationRuntime.get_interaction_state(conversation_id)
    and call .to_context() on the returned ConversationInteractionState.
    """
    return get_relationship_profile()


__all__ = [
    "RelationshipProfile",
    "ConversationInteractionState",
    "get_relationship_profile",
    "get_relationship_state",
]
