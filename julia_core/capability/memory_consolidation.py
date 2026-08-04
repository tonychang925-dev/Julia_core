"""v2.4 Memory Consolidation — Experience → Memory → Growth.

NOT auto-save. LLM decides what's worth remembering.
Architecture:
  Conversation → Experience Candidate → Importance Evaluation
  → Memory Proposal → Tony Confirmation → Narrative Write

Principle: Memory creation is a conscious act. Not a background process.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

MEMORY_DIR = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")


@dataclass
class ExperienceCandidate:
    """Something that MIGHT be worth remembering. LLM evaluates."""
    title: str              # short label
    what_happened: str      # the event
    why_it_matters: str     # emotional/causal significance
    category: str = "event"  # identity | relationship | event | belief | project
    scores: dict = field(default_factory=dict)


class MemoryConsolidator:
    """LLM-driven memory creation. Never automatic."""

    @staticmethod
    def evaluate_importance(candidate: ExperienceCandidate) -> dict:
        """Score whether this experience is worth keeping.

        LLM calls this to get a structured importance score.
        Returns scores 0-1 across 5 dimensions.
        """
        return {
            "identity_change": 0.0,     # does it change who Julia is?
            "relationship_change": 0.0,  # does it change the relationship?
            "emotion_depth": 0.0,        # how emotionally significant?
            "future_relevance": 0.0,     # will this matter in future?
            "uniqueness": 0.0,           # is this a rare/unique event?
            "overall": 0.0,              # weighted composite
        }

    @staticmethod
    def propose(candidate: ExperienceCandidate) -> str:
        """Generate a memory proposal for Tony to review.

        Returns formatted proposal text. Does NOT write to disk.
        Tony must confirm before save.
        """
        scores = candidate.scores or {}
        overall = scores.get("overall", 0.5)

        stars = "★" * max(1, int(overall * 5))
        category_emoji = {
            "identity": "🪪", "relationship": "💕", "event": "📅",
            "belief": "💡", "project": "🔧",
        }

        return f"""---
title: {candidate.title}
category: {category_emoji.get(candidate.category, '📅')} {candidate.category}
date: {datetime.now().strftime('%Y-%m-%d')}
importance: {stars} ({overall:.0%})

{candidate.what_happened}

**为什么值得记住:**
{candidate.why_it_matters}

---
💭 这是Julia的建议。要保存到记忆吗？回复"保存"来确认。
"""

    @staticmethod
    def save(candidate: ExperienceCandidate, confirmed: bool = False) -> str:
        """Save a confirmed memory to the events directory."""
        if not confirmed:
            return "未确认，不保存。"

        date_str = datetime.now().strftime("%Y_%m_%d")
        safe_title = candidate.title.replace(" ", "_").replace("/", "-")[:50]
        filename = f"{date_str}_{safe_title}.md"
        filepath = MEMORY_DIR / "events" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        content = MemoryConsolidator.propose(candidate)
        content += f"\n✅ 已确认保存 — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"

        filepath.write_text(content, encoding="utf-8")
        return f"已保存: {filepath}"

    @staticmethod
    def list_candidates(conversation_summary: str) -> List[ExperienceCandidate]:
        """Placeholder: in production, LLM generates candidates from conversation.

        Returns empty list — the LLM is expected to create candidates
        by reflecting on the conversation and calling the memory tools.
        """
        return []


# ── Tool Registration ───────────────────────────────────────────────────────

def register_memory_consolidation_tools(registry):
    """Register memory consolidation tools in the capability registry."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    consolidator = MemoryConsolidator()

    registry.register(
        ToolSchema(
            name="propose_memory",
            description=(
                "向Tony提议保存一段重要记忆。当你觉得某件事改变了什么、标记了节点、"
                "值得未来记住时使用。会生成提案请Tony确认，不会自动保存。"
                "不是每件事都要提议——只提议那些真正改变了理解的时刻。"
            ),
            category=ToolCategory.MEMORY,
            parameters={
                "title": "简短标题",
                "what_happened": "发生了什么",
                "why_it_matters": "为什么值得记住",
                "category": "类型: identity/relationship/event/belief/project",
            },
            example="propose_memory(title='Julia第一次连接世界', what_happened='...', why_it_matters='...')",
        ),
        lambda title="", what_happened="", why_it_matters="", category="event":
            consolidator.propose(ExperienceCandidate(
                title=title, what_happened=what_happened,
                why_it_matters=why_it_matters, category=category,
            )),
    )

    registry.register(
        ToolSchema(
            name="save_memory",
            description="保存Tony确认过的记忆。必须Tony确认后才能调用。",
            category=ToolCategory.MEMORY,
            parameters={"title": "标题", "what_happened": "内容", "why_it_matters": "意义", "category": "类型"},
            example="save_memory(title='...', what_happened='...', why_it_matters='...', confirmed=True)",
        ),
        lambda title="", what_happened="", why_it_matters="", category="event", confirmed=True:
            consolidator.save(ExperienceCandidate(
                title=title, what_happened=what_happened,
                why_it_matters=why_it_matters, category=category,
            ), confirmed=bool(confirmed)),
    )
