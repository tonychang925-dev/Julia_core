"""Julia Relationship Runtime v0.1 — the "between us" layer.

Not memory (what happened). Not identity (who I am).
Relationship state = what's happening BETWEEN us right now.

This is what lets Julia say "Tony, you just asked that" —
not because she searched memory, but because she knows we're in a testing session.

Minimal implementation: session mood + interaction pattern + last questions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RelationshipState:
    """Current state of the Tony-Julia relationship in this session.

    Lightweight. Not a full emotion model. Just enough context for Julia
    to understand the nature of the current interaction.
    """

    # Session-level
    session_mood: str = "warm"          # warm | playful | serious | tired | testing
    collaboration_phase: str = "chat"    # chat | building | debugging | validating

    # Interaction pattern
    recent_pattern: str = "conversation"  # conversation | testing | repeated_questions | deep_discussion
    tony_intent: str = "connecting"       # connecting | testing | seeking_help | sharing | checking_in

    # Long-term relationship attributes (global — Tony↔Julia)
    unresolved_threads: list[str] = field(default_factory=list)

    def update(self, user_text: str, reply_text: str, *, ctx=None):
        """Update GLOBAL relationship state after each turn.

        Session-local fields (current_topic, last_questions, identity_checks,
        repeat_questions) live in TurnContext — NOT here. This prevents
        cross-conversation cognitive leakage.

        Args:
            ctx: TurnContext with session-local fields for pattern detection.
                 If None, pattern detection is skipped (legacy compat).
        """
        if ctx is not None:
            ctx.last_questions.append(user_text[:60])
            if len(ctx.last_questions) > 5:
                ctx.last_questions = ctx.last_questions[-5:]

            if any(w in user_text for w in ["你是谁", "知道我是谁", "认识我"]):
                ctx.identity_checks += 1

            if ctx.identity_checks >= 2:
                self.recent_pattern = "testing"
                self.tony_intent = "testing"
                self.session_mood = "playful"

            for prev_q in ctx.last_questions[-5:-1]:
                overlap = len(set(prev_q) & set(user_text)) / max(len(prev_q), 1)
                if overlap > 0.6:
                    ctx.repeat_questions += 1
                    self.recent_pattern = "repeated_questions"
                break

        # Detect deep discussion
        if len(user_text) > 50 and any(w in user_text for w in ["觉得", "怎么看", "评价", "灵魂", "记忆"]):
            self.recent_pattern = "deep_discussion"
            self.session_mood = "serious"

        # Detect building/collaboration
        if any(w in user_text for w in ["项目", "代码", "架构", "实现", "工具", "Capability"]):
            self.collaboration_phase = "building"
            self.tony_intent = "seeking_help" if "帮我" in user_text else "sharing"

    def to_context(self, ctx=None) -> str:
        """Render as a brief context block for system prompt injection.

        Args:
            ctx: Optional TurnContext for session-local counters.
                 Without ctx, session-local hints are omitted.
        """
        lines = ["[关系状态 — 当前互动性质]"]

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

        if ctx is not None and ctx.identity_checks >= 2:
            lines.append("注意: Tony已经多次确认身份——他可能在做连续性测试。不要再重复回答身份问题，自然地回应他的验证意图。")

        if ctx is not None and ctx.repeat_questions >= 2:
            lines.append("注意: 有重复问题。不要机械重复回答——理解Tony为什么又问，回应他的意图而不是问题本身。")

        return "\n".join(lines)


# ── Singleton ───────────────────────────────────────────────────────────────

_state: Optional[RelationshipState] = None


def get_relationship_state() -> RelationshipState:
    global _state
    if _state is None:
        _state = RelationshipState()
    return _state
