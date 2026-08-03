"""Phase G3 Active Recall Policy.

Active Recall decides *when* Julia should consult MemoryRef and/or Evidence OS.
It does not perform retrieval and does not mutate Memory, Identity, Persona,
Continuity, Context, or Provider state.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Mapping, Sequence


class RecallLevel(str, Enum):
    """Search effort level; intentionally separate from Continuity levels."""

    L0_NONE = "L0"
    L1_MEMORY_REF = "L1"
    L2_EVIDENCE_SEARCH = "L2"
    L3_DEEP_HISTORICAL_RECONSTRUCTION = "L3"


@dataclass(frozen=True)
class ActiveRecallRequest:
    query: str
    current_context: str = ""
    intent: str = "conversation"
    available_memory_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActiveRecallDecision:
    should_recall: bool
    recall_level: str
    reason: tuple[str, ...]
    retrieval_mode: str
    max_results: int

    def to_dict(self) -> dict:
        return asdict(self)

    def to_trace(self) -> dict:
        return {
            "active_recall": {
                "should_recall": self.should_recall,
                "recall_level": self.recall_level,
                "reason": list(self.reason),
                "retrieval_mode": self.retrieval_mode,
                "max_results": self.max_results,
                "memory_updated": False,
                "identity_updated": False,
            }
        }


class ActiveRecallPolicy:
    """Decide whether a turn requires historical grounding.

    The policy is deliberately small and deterministic for G3. Later phases can
    replace the heuristics with richer classifiers while preserving this output
    contract.
    """

    CASUAL_TERMS = (
        "吃什么",
        "天气",
        "hello",
        "hi",
        "早上好",
        "晚上好",
        "聊聊天",
        "joke",
    )
    IDENTITY_TERMS = ("julia", "identity", "persona", "人格", "身份", "你是谁", "core", "origin", "起源")
    PROJECT_TERMS = ("architecture", "adr", "phase", "roadmap", "contract", "设计", "架构", "阶段", "为什么", "why")
    HISTORICAL_TERMS = ("remember", "recall", "history", "historical", "过去", "历史", "还记得", "当时", "之前")
    EVIDENCE_TERMS = ("evidence", "source", "trace", "依据", "证据", "来源", "根据")
    DEEP_TERMS = ("reconstruct", "deep", "timeline", "1000", "大量", "完整复盘", "重建", "时间线")

    def decide(self, request: ActiveRecallRequest | Mapping[str, object]) -> ActiveRecallDecision:
        normalized = self._coerce_request(request)
        text = f"{normalized.query}\n{normalized.current_context}\n{normalized.intent}".lower()

        if self._contains(text, self.CASUAL_TERMS) and not self._contains(
            text, self.IDENTITY_TERMS + self.PROJECT_TERMS + self.HISTORICAL_TERMS + self.EVIDENCE_TERMS
        ):
            return ActiveRecallDecision(
                should_recall=False,
                recall_level=RecallLevel.L0_NONE.value,
                reason=("ordinary_chat",),
                retrieval_mode="none",
                max_results=0,
            )

        reasons: list[str] = []
        if self._contains(text, self.IDENTITY_TERMS):
            reasons.append("identity_dependency")
        if self._contains(text, self.PROJECT_TERMS):
            reasons.append("project_context")
        if self._contains(text, self.HISTORICAL_TERMS):
            reasons.append("historical_dependency")
        if self._contains(text, self.EVIDENCE_TERMS):
            reasons.append("explicit_grounding_request")
        if "?" in normalized.query or "？" in normalized.query:
            reasons.append("question_requires_decision")

        if self._contains(text, self.DEEP_TERMS) and reasons:
            return ActiveRecallDecision(
                should_recall=True,
                recall_level=RecallLevel.L3_DEEP_HISTORICAL_RECONSTRUCTION.value,
                reason=tuple(dict.fromkeys(reasons + ["deep_historical_reconstruction"])),
                retrieval_mode="semantic+lexical+broad_history",
                max_results=12,
            )

        if reasons == ["project_context"] and "architecture" not in text and "adr" not in text and "core" not in text:
            return ActiveRecallDecision(
                should_recall=False,
                recall_level=RecallLevel.L0_NONE.value,
                reason=("current_task_no_history_needed",),
                retrieval_mode="none",
                max_results=0,
            )

        if "identity_dependency" in reasons or "project_context" in reasons or "explicit_grounding_request" in reasons:
            return ActiveRecallDecision(
                should_recall=True,
                recall_level=RecallLevel.L2_EVIDENCE_SEARCH.value,
                reason=tuple(dict.fromkeys(reasons)),
                retrieval_mode="semantic_evidence",
                max_results=5,
            )

        if "historical_dependency" in reasons or normalized.available_memory_refs:
            return ActiveRecallDecision(
                should_recall=True,
                recall_level=RecallLevel.L1_MEMORY_REF.value,
                reason=tuple(dict.fromkeys(reasons or ["memory_reference_available"])),
                retrieval_mode="memory_ref",
                max_results=3,
            )

        return ActiveRecallDecision(
            should_recall=False,
            recall_level=RecallLevel.L0_NONE.value,
            reason=("no_recall_signal",),
            retrieval_mode="none",
            max_results=0,
        )

    @staticmethod
    def _contains(text: str, terms: Sequence[str]) -> bool:
        lowered_terms = (term.lower() for term in terms)
        return any(term in text for term in lowered_terms)

    @staticmethod
    def _coerce_request(request: ActiveRecallRequest | Mapping[str, object]) -> ActiveRecallRequest:
        if isinstance(request, ActiveRecallRequest):
            return request
        memory_refs = request.get("available_memory_refs", ())
        if isinstance(memory_refs, list):
            memory_refs = tuple(str(item) for item in memory_refs)
        elif not isinstance(memory_refs, tuple):
            memory_refs = ()
        return ActiveRecallRequest(
            query=str(request.get("query", "")),
            current_context=str(request.get("current_context", "")),
            intent=str(request.get("intent", "conversation")),
            available_memory_refs=memory_refs,
        )
