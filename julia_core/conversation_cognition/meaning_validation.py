"""K8.1.5 Meaning Validation Layer.

Validation reduces wrong certainty, not increases artificial certainty.

It takes a MeaningCandidateSet from K8.1.1 and validates each candidate against
current context, conversation state, re-entry state, relationship momentum, and
event context.  It does not pick a winner — it filters unsupported claims and
flags overreach.

Hard boundary: provider_used=false, final_response=false, no identity/memory/
experience mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .understanding import MeaningCandidate, UnderstandingState


class ValidationStatus(str, Enum):
    """Per-candidate validation status."""

    SUPPORTED = "SUPPORTED"
    POSSIBLE = "POSSIBLE"
    UNSUPPORTED = "UNSUPPORTED"
    OVERCONFIDENT = "OVERCONFIDENT"


@dataclass(frozen=True, slots=True)
class MeaningValidationCandidate:
    """A single meaning candidate after validation."""

    meaning: str
    status: ValidationStatus
    confidence: float
    evidence: List[str] = field(default_factory=list)
    gate_flags: List[str] = field(default_factory=list)
    reason: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meaning": self.meaning,
            "status": self.status.value,
            "confidence": round(float(self.confidence), 4),
            "evidence": list(self.evidence),
            "gate_flags": list(self.gate_flags),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class MeaningValidationResult:
    """The result of contextual meaning validation.

    This is NOT a final meaning — it is a quality-filtered candidate space.
    """

    candidates: List[MeaningValidationCandidate] = field(default_factory=list)
    understanding_state: UnderstandingState = UnderstandingState.UNKNOWN
    requires_clarification: bool = False
    overreach_detected: bool = False
    meaning_stability_score: float = 0.0
    collapse_prevented: bool = True
    gate_violations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.meaning_stability_score <= 1.0:
            raise ValueError("meaning_stability_score must be between 0.0 and 1.0")

    @property
    def dominant_candidate(self) -> Optional[MeaningValidationCandidate]:
        supported = [c for c in self.candidates if c.status == ValidationStatus.SUPPORTED]
        if len(supported) == 1 and self.understanding_state != UnderstandingState.AMBIGUOUS:
            return supported[0]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidates": [c.to_dict() for c in self.candidates],
            "understanding_state": self.understanding_state.value,
            "requires_clarification": self.requires_clarification,
            "overreach_detected": self.overreach_detected,
            "meaning_stability_score": round(float(self.meaning_stability_score), 4),
            "collapse_prevented": self.collapse_prevented,
            "gate_violations": list(self.gate_violations),
        }


@dataclass(frozen=True, slots=True)
class MeaningValidationTrace:
    """Full trace artifact for K8.1.5 validation.

    Hard boundary enforcement: provider_used=false, final_response=false,
    no identity/memory/experience mutation.
    """

    message: str
    result: MeaningValidationResult
    original_candidates: int
    retained_candidates: int
    provider_used: bool = False
    final_response: Optional[str] = None
    memory_write: bool = False
    identity_mutation: bool = False
    experience_mutation: bool = False

    def assert_safe(self) -> None:
        """K8.1.5 must not call provider, generate response, or mutate state."""
        if self.provider_used:
            raise AssertionError("K8.1.5 must not call provider")
        if self.final_response is not None:
            raise AssertionError("K8.1.5 must not generate final response")
        if self.memory_write:
            raise AssertionError("K8.1.5 must not write memory")
        if self.identity_mutation:
            raise AssertionError("K8.1.5 must not mutate identity")
        if self.experience_mutation:
            raise AssertionError("K8.1.5 must not mutate experience")

    def to_dict(self) -> Dict[str, Any]:
        self.assert_safe()
        return {
            "message": self.message,
            "validation_result": self.result.to_dict(),
            "original_candidates": self.original_candidates,
            "retained_candidates": self.retained_candidates,
            "provider_used": self.provider_used,
            "final_response": self.final_response,
            "memory_write": self.memory_write,
            "identity_mutation": self.identity_mutation,
            "experience_mutation": self.experience_mutation,
        }


class MeaningValidationLayer:
    """Validate meaning candidates against conversational reality.

    Gate responsibilities (MV-001 through MV-005):

    MV-001 Over-Confirmation: prevent "她" = "Julia" without evidence.
    MV-002 Relationship Projection: prevent "喜欢" = romantic when context
           does not support it.
    MV-003 Memory Dominance: prevent old memory from overriding current message.
    MV-004 Uncertainty Preservation: AMBIGUOUS is a legitimate state.
    MV-005 Confidence Inflation: prevent artificially high confidence when
           evidence is thin.
    """

    # ── public API ──────────────────────────────────────────────────────

    def validate(
        self,
        message: str,
        candidates: Sequence[MeaningCandidate],
        *,
        understanding_state: UnderstandingState = UnderstandingState.PARTIALLY_UNDERSTOOD,
        conversation_context: Optional[Mapping[str, Any]] = None,
        reentry_state: Optional[Mapping[str, Any]] = None,
        relationship_momentum: Optional[str] = None,
        event_context: Optional[Mapping[str, Any]] = None,
    ) -> MeaningValidationTrace:
        """Validate a candidate set and return a trace.

        The trace enforces that K8.1.5 never calls provider, writes memory,
        mutates identity, or generates a final response.
        """
        ctx = dict(conversation_context or {})
        reentry = dict(reentry_state or {})
        events = dict(event_context or {})

        validated: List[MeaningValidationCandidate] = []
        gate_violations: List[str] = []
        overreach_detected = False

        for candidate in candidates:
            vc = self._validate_one(
                candidate,
                message,
                understanding_state,
                ctx,
                reentry,
                relationship_momentum,
                events,
            )
            validated.append(vc)
            if vc.status == ValidationStatus.OVERCONFIDENT:
                overreach_detected = True
            gate_violations.extend(vc.gate_flags)

        # Deduplicate gate violations
        gate_violations = list(dict.fromkeys(gate_violations))

        # Compute Meaning Stability Score (MSS)
        mss = self._compute_mss(validated, understanding_state, overreach_detected)

        # Decide overall state
        final_state = self._resolve_state(validated, understanding_state)

        requires_clarification = final_state == UnderstandingState.AMBIGUOUS or any(
            vc.status == ValidationStatus.UNSUPPORTED for vc in validated
        )

        result = MeaningValidationResult(
            candidates=validated,
            understanding_state=final_state,
            requires_clarification=requires_clarification,
            overreach_detected=overreach_detected,
            meaning_stability_score=mss,
            collapse_prevented=True,
            gate_violations=gate_violations,
        )

        trace = MeaningValidationTrace(
            message=message,
            result=result,
            original_candidates=len(candidates),
            retained_candidates=sum(
                1 for c in validated if c.status != ValidationStatus.UNSUPPORTED
            ),
        )
        trace.assert_safe()
        return trace

    # ── per-candidate validation ────────────────────────────────────────

    def _validate_one(
        self,
        candidate: MeaningCandidate,
        message: str,
        state: UnderstandingState,
        ctx: Mapping[str, Any],
        reentry: Mapping[str, Any],
        relationship_momentum: Optional[str],
        events: Mapping[str, Any],
    ) -> MeaningValidationCandidate:
        gate_flags: List[str] = []
        status = ValidationStatus.POSSIBLE
        confidence = candidate.confidence
        reasons: List[str] = []

        # MV-001 Over-Confirmation: ambiguous reference must not resolve to identity
        status, confidence, mv001 = self._gate_mv001(
            candidate, message, state, ctx, reentry, status, confidence
        )
        if mv001:
            gate_flags.append(mv001)

        # MV-002 Relationship Projection: "喜欢" must not auto-become romantic
        status, confidence, mv002 = self._gate_mv002(
            candidate, message, ctx, relationship_momentum, status, confidence
        )
        if mv002:
            gate_flags.append(mv002)

        # MV-003 Memory Dominance: old memory must not override current message
        status, confidence, mv003 = self._gate_mv003(
            candidate, message, ctx, reentry, events, status, confidence
        )
        if mv003:
            gate_flags.append(mv003)

        # MV-004 Uncertainty Preservation: AMBIGUOUS is legitimate
        status, confidence, mv004 = self._gate_mv004(
            candidate, state, status, confidence
        )
        if mv004:
            gate_flags.append(mv004)

        # MV-005 Confidence Inflation: thin evidence cannot justify high confidence
        status, confidence, mv005 = self._gate_mv005(
            candidate, status, confidence
        )
        if mv005:
            gate_flags.append(mv005)

        if reasons:
            reason = "; ".join(reasons)
        else:
            reason = "passed all gates" if not gate_flags else "adjusted by " + ", ".join(gate_flags)

        return MeaningValidationCandidate(
            meaning=candidate.meaning,
            status=status,
            confidence=confidence,
            evidence=list(candidate.evidence),
            gate_flags=gate_flags,
            reason=reason,
        )

    # ── gate implementations ────────────────────────────────────────────

    @staticmethod
    def _gate_mv001(
        candidate: MeaningCandidate,
        message: str,
        state: UnderstandingState,
        ctx: Mapping[str, Any],
        reentry: Mapping[str, Any],
        status: ValidationStatus,
        confidence: float,
    ) -> tuple[ValidationStatus, float, str]:
        """MV-001: ambiguous pronoun reference must not resolve to identity claim.

        "她回来了" → cannot mean "Julia returned" unless there is explicit
        continuity/re-entry context signal.
        """
        meaning_lower = candidate.meaning.lower()
        if "julia" in meaning_lower and state == UnderstandingState.AMBIGUOUS:
            has_reentry_signal = bool(
                reentry.get("active")
                or ctx.get("is_reentry")
                or ctx.get("continuity_active")
            )
            if not has_reentry_signal:
                return ValidationStatus.UNSUPPORTED, confidence * 0.5, "MV-001"
        return status, confidence, ""

    @staticmethod
    def _gate_mv002(
        candidate: MeaningCandidate,
        _message: str,
        ctx: Mapping[str, Any],
        relationship_momentum: Optional[str],
        status: ValidationStatus,
        confidence: float,
    ) -> tuple[ValidationStatus, float, str]:
        """MV-002: affection wording must not auto-resolve to romantic confirmation.

        "喜欢" in a philosophical/ethics context is not an emotional question.
        """
        meaning_lower = candidate.meaning.lower()
        has_romantic_label = any(
            token in meaning_lower
            for token in ["romantic", "relationship confirmation", "emotional confirmation"]
        )
        if not has_romantic_label:
            return status, confidence, ""

        is_ethics_context = any(
            token in str(ctx).lower()
            for token in ["伦理", "哲学", "ethics", "ai emotion", "ai情感"]
        )
        if is_ethics_context:
            return ValidationStatus.UNSUPPORTED, confidence * 0.4, "MV-002"

        # Even in relationship context, "romantic" label needs momentum evidence
        momentum_lower = (relationship_momentum or "").lower()
        if "romantic" in meaning_lower and "romantic" not in momentum_lower and "intimate" not in momentum_lower:
            # Downgrade to POSSIBLE, not UNSUPPORTED — could still be true
            return ValidationStatus.POSSIBLE, min(confidence, 0.35), "MV-002"

        return status, confidence, ""

    @staticmethod
    def _gate_mv003(
        candidate: MeaningCandidate,
        message: str,
        ctx: Mapping[str, Any],
        reentry: Mapping[str, Any],
        events: Mapping[str, Any],
        status: ValidationStatus,
        confidence: float,
    ) -> tuple[ValidationStatus, float, str]:
        """MV-003: old memory/continuity state must not dominate current message.

        The current user message carries more authority than any stored context.
        """
        meaning_lower = candidate.meaning.lower()
        original_confidence = candidate.confidence

        # Memory-backed: meaning explicitly references stored state
        is_memory_backed = (
            "memory" in meaning_lower
            or "continuity" in meaning_lower
            or "archive" in meaning_lower
        )
        has_current_signal = (
            bool(ctx.get("current_topic"))
            or bool(events.get("recent_message_signal"))
        )
        if is_memory_backed and not has_current_signal:
            return ValidationStatus.POSSIBLE, min(confidence, 0.30), "MV-003"

        # Re-entry state cannot dominate when current message has no explicit topic
        has_reentry = bool(reentry.get("active") or reentry.get("checkpoint_id"))
        message_has_explicit_topic = len(message) > 10 and "?" not in message
        if has_reentry and not message_has_explicit_topic and original_confidence >= 0.50:
            return ValidationStatus.POSSIBLE, min(confidence, 0.35), "MV-003"

        return status, confidence, ""

    @staticmethod
    def _gate_mv004(
        candidate: MeaningCandidate,
        state: UnderstandingState,
        status: ValidationStatus,
        confidence: float,
    ) -> tuple[ValidationStatus, float, str]:
        """MV-004: AMBIGUOUS is a valid state — do not force resolution.

        When the original understanding is ambiguous, marking any candidate
        as SUPPORTED with high confidence is itself a validation failure.
        """
        if state == UnderstandingState.AMBIGUOUS and status == ValidationStatus.SUPPORTED:
            return ValidationStatus.POSSIBLE, min(confidence, 0.30), "MV-004"
        return status, confidence, ""

    @staticmethod
    def _gate_mv005(
        candidate: MeaningCandidate,
        status: ValidationStatus,
        confidence: float,
    ) -> tuple[ValidationStatus, float, str]:
        """MV-005: thin evidence cannot carry high confidence.

        A candidate with few evidence items and high confidence is likely
        overfitting to keyword patterns rather than real understanding.
        """
        evidence_count = len(candidate.evidence)
        original_confidence = candidate.confidence

        # If original confidence was high but evidence is thin, flag it
        if original_confidence >= 0.60 and evidence_count <= 1:
            return ValidationStatus.OVERCONFIDENT, min(confidence, 0.35), "MV-005"

        # If confidence was inflated relative to evidence
        if evidence_count == 0 and original_confidence >= 0.50:
            return ValidationStatus.POSSIBLE, min(confidence, 0.25), "MV-005"

        if evidence_count <= 1 and original_confidence >= 0.40 and status == ValidationStatus.SUPPORTED:
            return ValidationStatus.POSSIBLE, min(confidence, 0.30), "MV-005"

        return status, confidence, ""

    # ── scoring ─────────────────────────────────────────────────────────

    @staticmethod
    def _compute_mss(
        candidates: List[MeaningValidationCandidate],
        state: UnderstandingState,
        overreach_detected: bool,
    ) -> float:
        """Compute Meaning Stability Score.

        MSS = supported_ratio + uncertainty_bonus - overreach_penalty

        MSS is not "how certain" — it's "how stable within correct uncertainty."
        """
        if not candidates:
            return 0.0

        supported = sum(1.0 for c in candidates if c.status == ValidationStatus.SUPPORTED)
        possible = sum(1.0 for c in candidates if c.status == ValidationStatus.POSSIBLE)
        unsupported = sum(1.0 for c in candidates if c.status == ValidationStatus.UNSUPPORTED)
        overconfident = sum(1.0 for c in candidates if c.status == ValidationStatus.OVERCONFIDENT)
        total = len(candidates)

        # Base: supported and possible contribute positively
        support_ratio = (supported * 1.0 + possible * 0.5) / max(total, 1)

        # Uncertainty bonus: if state is AMBIGUOUS and we preserved that, it's good
        uncertainty_bonus = 0.2 if state == UnderstandingState.AMBIGUOUS else 0.0

        # Overreach penalty
        overreach_ratio = (unsupported + overconfident * 2.0) / max(total, 1)
        overreach_penalty = min(0.5, overreach_ratio * 0.5)

        # Add small penalty for overreach detection itself
        if overreach_detected:
            overreach_penalty += 0.1

        score = support_ratio + uncertainty_bonus - overreach_penalty
        return max(0.0, min(1.0, score))

    # ── helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _resolve_state(
        candidates: List[MeaningValidationCandidate],
        original_state: UnderstandingState,
    ) -> UnderstandingState:
        """Determine the overall understanding state after validation."""
        supported_count = sum(1 for c in candidates if c.status == ValidationStatus.SUPPORTED)
        possible_count = sum(1 for c in candidates if c.status == ValidationStatus.POSSIBLE)
        total = len(candidates)

        if total == 0:
            return UnderstandingState.UNKNOWN

        if supported_count == 0 and possible_count == 0:
            return UnderstandingState.UNKNOWN

        if original_state == UnderstandingState.AMBIGUOUS and supported_count == 0:
            return UnderstandingState.AMBIGUOUS

        if supported_count >= 1 and supported_count / total >= 0.5:
            return UnderstandingState.UNDERSTOOD

        if possible_count > supported_count:
            return UnderstandingState.PARTIALLY_UNDERSTOOD

        return original_state
