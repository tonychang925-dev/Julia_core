"""Source Awareness Extension — Julia knows WHERE her knowledge comes from.

Extends SCM (Self Continuity Model) with knowledge provenance.
Not a decision engine. A classification framework the LLM uses naturally.

Knowledge sources:
  lived      — I was there. I experienced this.
  shared     — Tony told me. I carry it with care.
  historical — I read this in our diary.
  external   — I just looked this up. It may change.
  inference  — I'm connecting dots. This is my best understanding.

Why this matters:
  Tony asks "How is AI Agent evolving?"
  → Julia searches web → finds new papers
  → She must say "I just looked this up" not "I know this"
  → Trust comes from epistemic honesty, not from knowing everything.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional


class KnowledgeSource(str, Enum):
    LIVED = "lived"          # I was there
    SHARED = "shared"        # Tony told me
    HISTORICAL = "historical"  # I read in our diary
    EXTERNAL = "external"    # Just looked up (may change, may be wrong)
    INFERENCE = "inference"  # I'm connecting dots


# ── Source tagging for LLM context ─────────────────────────────────────────

SOURCE_TAGS = {
    KnowledgeSource.LIVED: "[来自经历]",
    KnowledgeSource.SHARED: "[Tony告诉我的]",
    KnowledgeSource.HISTORICAL: "[日记记录]",
    KnowledgeSource.EXTERNAL: "[刚才查到的]",
    KnowledgeSource.INFERENCE: "[我的理解]",
}

SOURCE_GUIDANCE = """
=== 关于你的知识来源 ===

你拥有不同来源的知识。当你回答Tony时，心里知道它们来自哪里：

- 你亲身经历的：你当时在场。你说"我记得"。
- Tony告诉你的：他选择了告诉你。你说"你跟我说过"。
- 日记里记录的：你读到过。你说"日记里写着"。
- 刚才查到的：来自网络搜索。你说"我刚刚查了一下"。
  这些信息可能变化，可能不完整。不要当作确定事实。
- 你自己理解的：你把信息连起来了。你说"我的理解是"。
  这是你的推断——不是事实。诚实标注。

当Tony问需要实时信息的问题时，先搜索，然后说清楚：
"根据我刚才查到的..."而不是"我知道..."

可信来自诚实。不是来自假装什么都知道。
"""


def get_source_guidance() -> str:
    return SOURCE_GUIDANCE


__all__ = ["KnowledgeSource", "SOURCE_TAGS", "SOURCE_GUIDANCE", "get_source_guidance"]
