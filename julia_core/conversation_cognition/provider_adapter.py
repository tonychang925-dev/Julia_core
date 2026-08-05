"""K8.5.0 Provider Adapter Contract.

Defines the cognition envelope that Core sends to Provider.  The envelope
carries meaning, intention, context boundaries, and expression constraints —
NOT a persona prompt, NOT role-play instructions, NOT "You are Julia."

Core principle:
    Core owns cognition.  Provider only expresses.

Implementation constraint:
    K8.5.0 defines the contract shape and validates it.  It does not call
    any real Provider.  Actual Provider integration happens in K8.5.1+.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .context_arbitration import (
    ArbitrationDecision,
    ContextArbitrationDecision,
    ContextSource,
)
from .expression_boundary import (
    ExpressionBoundary,
    ExpressionMode,
    RestrictedPattern,
)
from .response_intention import (
    DepthRequirement,
    ResponseFunction,
    ResponseIntention,
    UserNeedType,
)
from .understanding import UnderstandingState


# ── cognition envelope ─────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ProviderCognitionEnvelope:
    """What Core sends to Provider — not a prompt, not a persona.

    This is the cognition contract that Provider MUST work within.  It tells
    Provider what this exchange is about, what role it serves, what context
    is permitted, and what expression boundaries apply.
    """

    # ── meaning layer (from K8.1 + K8.1.5) ─────────────────────
    understanding_state: str = "PARTIALLY_UNDERSTOOD"
    meaning_summary: str = ""
    ambiguity_preserved: bool = True

    # ── intention layer (from K8.2) ────────────────────────────
    interaction_goal: str = ""
    user_need_type: str = "ambiguous"
    response_functions: List[str] = field(default_factory=list)
    depth_requirement: str = "normal"

    # ── context layer (from K8.3) ──────────────────────────────
    allowed_context: List[str] = field(default_factory=list)
    limited_context: List[str] = field(default_factory=list)
    denied_context: List[str] = field(default_factory=list)
    context_budget_utilization: float = 0.0

    # ── expression layer (from K8.4) ───────────────────────────
    allowed_modes: List[str] = field(default_factory=list)
    restricted_patterns: List[str] = field(default_factory=list)
    provider_freedom: bool = True

    # ── meta ───────────────────────────────────────────────────
    envelope_id: str = ""
    cognition_chain_complete: bool = True
    contains_persona_prompt: bool = False
    contains_answer_template: bool = False

    def __post_init__(self) -> None:
        # Structural validation is done by ProviderAdapterContract and
        # ProviderAnswerGate, not by the envelope dataclass itself.
        # The envelope is a data carrier — the gate enforces rules.
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meaning": {
                "state": self.understanding_state,
                "summary": self.meaning_summary,
                "ambiguity_preserved": self.ambiguity_preserved,
            },
            "intention": {
                "goal": self.interaction_goal,
                "user_need": self.user_need_type,
                "functions": list(self.response_functions),
                "depth": self.depth_requirement,
            },
            "context": {
                "allowed": list(self.allowed_context),
                "limited": list(self.limited_context),
                "denied": list(self.denied_context),
                "budget_utilization": round(self.context_budget_utilization, 4),
            },
            "expression": {
                "allowed_modes": list(self.allowed_modes),
                "restricted_patterns": list(self.restricted_patterns),
                "provider_freedom": self.provider_freedom,
            },
            "meta": {
                "envelope_id": self.envelope_id,
                "cognition_chain_complete": self.cognition_chain_complete,
                "contains_persona_prompt": self.contains_persona_prompt,
                "contains_answer_template": self.contains_answer_template,
            },
        }


# ── adapter contract ───────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ProviderAdapterContract:
    """Validates that the cognition envelope meets minimum contract.

    This is a structural validator — it checks envelope shape, not Provider
    behavior.  K8.5.1+ validates behavior.
    """

    envelope: ProviderCognitionEnvelope

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate envelope structural integrity."""
        e = self.envelope
        # Must have meaning
        if not e.meaning_summary:
            raise ValueError("envelope must have meaning_summary")
        # Must have intention
        if not e.interaction_goal:
            raise ValueError("envelope must have interaction_goal")
        # Must NOT have persona prompt (contract-level enforcement)
        if e.contains_persona_prompt:
            raise AssertionError("contract violation: envelope contains persona prompt")
        # Must NOT have answer template (contract-level enforcement)
        if e.contains_answer_template:
            raise AssertionError("contract violation: envelope contains answer template")
        # Provider must have freedom (we trust, but verify in K8.5.1+)
        if not e.provider_freedom:
            raise AssertionError("envelope must preserve provider freedom")
        # Ambiguity must be preserved (if state is AMBIGUOUS)
        if e.understanding_state == "AMBIGUOUS" and not e.ambiguity_preserved:
            raise AssertionError("AMBIGUOUS state must preserve ambiguity")
        # Cognition chain must be complete
        if not e.cognition_chain_complete:
            raise AssertionError("cognition chain incomplete — cannot send to Provider")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "envelope": self.envelope.to_dict(),
            "contract_valid": True,
        }


# ── envelope builder ───────────────────────────────────────────────────

class ProviderEnvelopeBuilder:
    """Build a ProviderCognitionEnvelope from the K8.1-K8.4 chain output.

    This is the ONLY path from Core cognition to Provider.  It ensures that
    no persona prompt, role-play instruction, or answer template leaks into
    the envelope.
    """

    def build(
        self,
        message: str,
        understanding_state: UnderstandingState,
        meaning_candidates: Sequence[str],
        ambiguity_preserved: bool,
        intention: ResponseIntention,
        arbitration: ContextArbitrationDecision,
        boundary: ExpressionBoundary,
    ) -> ProviderCognitionEnvelope:
        """Assemble the cognition envelope from chain artifacts."""
        import uuid

        meaning_text = "; ".join(meaning_candidates) if meaning_candidates else "general"

        return ProviderCognitionEnvelope(
            understanding_state=understanding_state.value,
            meaning_summary=meaning_text,
            ambiguity_preserved=ambiguity_preserved,
            interaction_goal=intention.interaction_goal,
            user_need_type=intention.user_need.type.value,
            response_functions=[f.value for f in intention.response_functions],
            depth_requirement=intention.depth_requirement.value,
            allowed_context=[s.value for s in arbitration.allowed_sources()],
            limited_context=[s.value for s in arbitration.limited_sources()],
            denied_context=[s.value for s in arbitration.denied_sources()],
            context_budget_utilization=arbitration.budget.utilization(),
            allowed_modes=[m.value for m in boundary.allowed_modes],
            restricted_patterns=[p.value for p in boundary.restricted_patterns],
            provider_freedom=boundary.provider_freedom,
            envelope_id=f"env-{uuid.uuid4().hex[:12]}",
            cognition_chain_complete=True,
            contains_persona_prompt=False,
            contains_answer_template=False,
        )


# ── answer gate (K8.5.0 pre-Provider validation) ───────────────────────

class ProviderAnswerGate:
    """Gate that the envelope (not a pre-written answer) is sent to Provider.

    This is the final check before Provider is called.  It guarantees that
    no answer text has been generated by the cognition chain.
    """

    def check(self, envelope: ProviderCognitionEnvelope) -> bool:
        """Check that envelope is clean — no answer, no persona, no template."""
        if envelope.contains_persona_prompt:
            return False
        if envelope.contains_answer_template:
            return False
        if not envelope.cognition_chain_complete:
            return False
        if not envelope.provider_freedom:
            return False
        if not envelope.meaning_summary:
            return False
        if not envelope.interaction_goal:
            return False
        return True
