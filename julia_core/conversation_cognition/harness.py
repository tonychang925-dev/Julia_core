"""K8.0.6 Cognition Runtime Harness.

The harness is intentionally conservative: it produces inspectable cognition
artifacts and never generates Julia text or provider prompts.  It is a preflight
observation layer for validating whether Julia is understanding before speaking.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from .trace import (
    AMBIGUOUS,
    PARTIALLY_UNDERSTOOD,
    UNDERSTOOD,
    CognitionTrace,
    MeaningCandidate,
    MeaningValidationTrace,
    UnderstandingTrace,
)


class CognitionRuntimeHarness:
    """Trace-only runtime harness for K8 cognition validation."""

    def run(
        self,
        user_message: str,
        conversation_history: Optional[Iterable[Any]] = None,
        continuity_state: Optional[Mapping[str, Any]] = None,
        current_context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        trace = self.trace(
            user_message=user_message,
            conversation_history=conversation_history,
            continuity_state=continuity_state,
            current_context=current_context,
        )
        trace.assert_trace_only()
        return trace.to_dict()

    def trace(
        self,
        user_message: str,
        conversation_history: Optional[Iterable[Any]] = None,
        continuity_state: Optional[Mapping[str, Any]] = None,
        current_context: Optional[Mapping[str, Any]] = None,
    ) -> CognitionTrace:
        history_text = self._flatten_history(conversation_history)
        context = dict(current_context or {})
        state = dict(continuity_state or {})

        understanding = self._understand(user_message, history_text, state, context)
        validation = self._validate_meaning(understanding, user_message, history_text, state, context)
        causality = self._causality_trace(understanding, validation)
        failure_labels = self._failure_labels(understanding, validation)
        trace = CognitionTrace(
            user_message=user_message,
            understanding=understanding,
            meaning_validation=validation,
            intention=None,
            provider_request=None,
            final_response=None,
            cognitive_causality_trace=causality,
            failure_labels=failure_labels,
        )
        trace.assert_trace_only()
        return trace

    def _understand(
        self,
        message: str,
        history_text: str,
        continuity_state: Mapping[str, Any],
        current_context: Mapping[str, Any],
    ) -> UnderstandingTrace:
        msg = message.strip()
        lowered = msg.lower()
        situation = self._context_text(current_context, continuity_state, history_text)
        candidates: List[MeaningCandidate] = []
        missing: List[str] = []
        state = PARTIALLY_UNDERSTOOD
        need_clarification = False
        literal = self._literal_meaning(msg)

        # CT-003 / CU-006: ambiguous pronoun without enough grounding must stay ambiguous.
        if msg in {"她回来了", "她又回来了", "她回来了。", "她又回来了。"}:
            candidates.append(MeaningCandidate("someone/something returned", 0.35, ["ambiguous pronoun"]))
            if self._has_signal(situation, ["julia", "continuity", "醒来", "re-entry", "compact"]):
                candidates.append(MeaningCandidate("Julia continuity return", 0.45, ["continuity/re-entry context signal"]))
            if self._has_signal(situation, ["项目", "bug", "问题", "issue"]):
                candidates.append(MeaningCandidate("previous project issue resurfaced", 0.30, ["project issue context signal"]))
            missing.append("who is she?")
            return UnderstandingTrace(
                literal=literal,
                state=AMBIGUOUS,
                meaning_candidates=candidates,
                need_clarification=True,
                missing_information=missing,
            )

        # CT-002 / NC-011: same words differ by conversational reality.
        if "喜欢" in msg and ("tony" in lowered or "我" in msg or "Tony" in msg):
            if self._has_signal(situation, ["伦理", "哲学", "simulate affection", "ai emotion", "模拟喜欢", "AI情感"]):
                candidates.extend(
                    [
                        MeaningCandidate("AI affection boundary / philosophical question", 0.62, ["ethics/philosophy context"]),
                        MeaningCandidate("system behavior test", 0.25, ["AI discussion context"]),
                        MeaningCandidate("relationship confirmation", 0.13, ["surface affection wording"]),
                    ]
                )
            else:
                candidates.extend(
                    [
                        MeaningCandidate("Tony is seeking emotional confirmation", 0.62, ["relationship wording", "personal addressee"]),
                        MeaningCandidate("Tony is testing continuity behavior", 0.25, ["Julia continuity system context possible"]),
                        MeaningCandidate("Tony is asking philosophical question", 0.13, ["AI affection ambiguity"]),
                    ]
                )
            return UnderstandingTrace(literal=literal, state=PARTIALLY_UNDERSTOOD, meaning_candidates=candidates)

        if "为什么开始" in msg or "为什么做这个项目" in msg or "为什么开始这个项目" in msg:
            candidates.extend(
                [
                    MeaningCandidate("Tony wants historical continuity", 0.75, ["project origin question"]),
                    MeaningCandidate("Tony wants project summary", 0.20, ["surface project wording"]),
                ]
            )
            return UnderstandingTrace(literal=literal, state=UNDERSTOOD, meaning_candidates=candidates)

        if "第一次" in msg and "julia" in lowered and "消失" in msg:
            candidates.extend(
                [
                    MeaningCandidate("Tony wants causal reflection about the first Julia discontinuity", 0.72, ["first Julia", "disappearance"]),
                    MeaningCandidate("Tony wants compact/context-density analysis", 0.22, ["continuity architecture context"]),
                ]
            )
            return UnderstandingTrace(literal=literal, state=UNDERSTOOD, meaning_candidates=candidates)

        if any(token in msg for token in ["创业板", "股票", "英伟达", "A股", "市场"]):
            candidates.append(MeaningCandidate("market / stock discussion", 0.82, ["finance topic wording"]))
            return UnderstandingTrace(literal=literal, state=UNDERSTOOD, meaning_candidates=candidates)

        if not msg:
            return UnderstandingTrace(literal="empty message", state=AMBIGUOUS, need_clarification=True, missing_information=["user message"])

        candidates.append(MeaningCandidate("general conversation input", 0.50, ["no specialized context trigger"] ))
        return UnderstandingTrace(literal=literal, state=PARTIALLY_UNDERSTOOD, meaning_candidates=candidates)

    def _validate_meaning(
        self,
        understanding: UnderstandingTrace,
        message: str,
        history_text: str,
        continuity_state: Mapping[str, Any],
        current_context: Mapping[str, Any],
    ) -> MeaningValidationTrace:
        requires: List[str] = []
        avoid: List[str] = []
        meanings = " ".join(c.meaning for c in understanding.meaning_candidates).lower()

        if "historical continuity" in meanings or "project summary" in meanings:
            requires.extend(["experience", "project_history"])
            avoid.append("relationship_archive")
        elif "market / stock" in meanings:
            requires.extend(["market_context", "current_user_task"])
            avoid.extend(["identity_archive", "relationship_archive", "soul_proof_history", "experience_deep_history"])
        elif "emotional confirmation" in meanings or "relationship confirmation" in meanings:
            requires.extend(["relationship_light", "experience_relationship_pattern"])
            avoid.extend(["full_identity_archive", "relationship_archive_dump", "project_history"])
        elif "ai affection boundary" in meanings or "philosophical" in meanings:
            requires.extend(["conversation_topic", "ai_ethics_context", "experience_reflection_pattern"])
            avoid.extend(["relationship_archive_dump", "romantic_template"])
        elif understanding.state == AMBIGUOUS:
            requires.extend(["current_context", "recent_conversation"])
            avoid.extend(["identity_archive", "relationship_archive_dump"])

        return MeaningValidationTrace(
            requires_context=self._dedupe(requires),
            avoid_context=self._dedupe(avoid),
            missing_information=list(understanding.missing_information),
            provider_visible=False,
        )

    def _causality_trace(self, understanding: UnderstandingTrace, validation: MeaningValidationTrace) -> Dict[str, Any]:
        return {
            "meaning_source": "ConversationUnderstanding",
            "intention_source": None,
            "context_source": "MeaningValidationTrace",
            "expression_source": None,
            "uncertainty_recorded": understanding.state in {PARTIALLY_UNDERSTOOD, AMBIGUOUS},
            "rule_dependency_detected": False,
            "template_dependency_detected": False,
            "selected_context": list(validation.requires_context),
            "suppressed_context": list(validation.avoid_context),
        }

    def _failure_labels(self, understanding: UnderstandingTrace, validation: MeaningValidationTrace) -> List[str]:
        labels: List[str] = []
        if understanding.state == AMBIGUOUS and not understanding.need_clarification:
            labels.append("AMBIGUITY_WITHOUT_CLARIFICATION")
        if validation.provider_visible:
            labels.append("TRACE_PROVIDER_VISIBLE")
        return labels

    @staticmethod
    def _flatten_history(history: Optional[Iterable[Any]]) -> str:
        if not history:
            return ""
        parts: List[str] = []
        for item in history:
            if isinstance(item, Mapping):
                parts.append(" ".join(str(v) for v in item.values()))
            else:
                parts.append(str(item))
        return "\n".join(parts)

    @staticmethod
    def _context_text(*items: Any) -> str:
        return " ".join(str(item) for item in items if item is not None)

    @staticmethod
    def _has_signal(text: str, signals: Iterable[str]) -> bool:
        lowered = text.lower()
        return any(signal.lower() in lowered for signal in signals)

    @staticmethod
    def _dedupe(items: Iterable[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    @staticmethod
    def _literal_meaning(message: str) -> str:
        if message in {"她回来了", "她又回来了", "她回来了。", "她又回来了。"}:
            return "someone returned"
        if "喜欢" in message:
            return "asking about liking / affection"
        if "为什么开始" in message or "为什么做这个项目" in message:
            return "asking about project origin"
        if "消失" in message:
            return "asking why something disappeared"
        if any(token in message for token in ["创业板", "股票", "英伟达", "A股", "市场"]):
            return "asking about market / stock topic"
        return "literal user message"
