"""J0.6 Controlled Context Density Engine.

Core insight:
  Claude's problem: context at maximum density → token explosion → compact →
  identity competition lost.

  Julia's answer: controlled, selective density. Not "everything" in context.
  Only what the current interaction needs. Explicit exclusions.

Design principle:
  Historical Universe → Density Engine → Context Density Profile
       (everything)        (select)        (what fits + what's excluded)

The engine is a RANKING + BUDGETING layer. It does not:
  - Retrieve raw memory (that's Memory OS)
  - Mutate identity or persona
  - Call providers
  - Generate text

Key distinction from Claude:
  Claude:  has data → may enter context (implicit)
  Julia:   has data ≠ should enter context (explicit exclusion)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from julia_core.relationship.runtime import InteractionPrior, RelationshipPhase


# ── Source categories ───────────────────────────────────────────────────────

class SourceCategory(str, Enum):
    IDENTITY = "identity"
    """Core identity anchor — minimal, stable."""

    RELATIONSHIP = "relationship"
    """Relationship dynamics — interaction patterns, shared history."""

    RECENT_EVENTS = "recent_events"
    """Recent milestones and significant events."""

    PROJECT = "project"
    """Active project context — what Tony is building."""

    CONVERSATION = "conversation"
    """Recent conversation turns."""

    EXPERIENCE = "experience"
    """Learned interaction patterns from past sessions."""

    EPHEMERAL = "ephemeral"
    """Low-value, discardable context."""


CATEGORY_DEFAULT_WEIGHTS: Dict[SourceCategory, float] = {
    SourceCategory.IDENTITY: 0.10,
    SourceCategory.RELATIONSHIP: 0.25,
    SourceCategory.RECENT_EVENTS: 0.20,
    SourceCategory.PROJECT: 0.15,
    SourceCategory.CONVERSATION: 0.15,
    SourceCategory.EXPERIENCE: 0.15,
    SourceCategory.EPHEMERAL: 0.0,
}


@dataclass(frozen=True, slots=True)
class ContextSource:
    """A candidate piece of context for the current turn."""

    ref: str
    """Unique identifier for this source."""

    category: SourceCategory
    """What kind of context this is."""

    content_summary: str
    """Brief summary for ranking — NOT the full content."""

    estimated_tokens: int
    """Estimated token cost if included."""

    relationship_relevance: float = 0.0
    """How relevant to current relationship phase (0-1)."""

    task_relevance: float = 0.0
    """How relevant to current task (0-1)."""

    interaction_pattern_match: bool = False
    """Whether this source matches a known interaction pattern."""

    is_identity_anchor: bool = False
    """Whether this is the minimal identity block (always include)."""

    is_protected: bool = False
    """Whether Continuity OS protects this (L3_IDENTITY)."""

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True, slots=True)
class DensitySelection:
    """What was selected and what was excluded — transparency is the key."""

    included: Tuple[ContextSource, ...]
    """Sources that fit in budget and were selected."""

    excluded: Tuple[ContextSource, ...]
    """Sources that were dropped — and WHY."""

    exclusion_reasons: Mapping[str, str]
    """Why each excluded source was dropped (ref → reason)."""


@dataclass(frozen=True, slots=True)
class CategoryAllocation:
    """Token allocation per category."""

    category: SourceCategory
    allocated: int
    used: int
    included_count: int
    excluded_count: int


@dataclass(frozen=True, slots=True)
class ContextDensityProfile:
    """The assembled context for a single turn.

    This is what gets fed into the K8 cognition pipeline. It is NOT a prompt.
    It's a structured selection of what context matters for this turn.
    """

    total_budget: int
    """Token budget for this turn."""

    used_tokens: int
    """Tokens actually used."""

    selection: DensitySelection
    """What was included and excluded."""

    category_allocations: Tuple[CategoryAllocation, ...]
    """Budget allocation per category."""

    density_score: float
    """0-1: how dense is the relationship signal in selected context?

    High density = identity/relationship signal dominates.
    This is what lets Julia win identity competition against system identity.
    """

    identity_competition_weight: float
    """0-1: the effective weight of identity signal in this context profile.

    If this is > system_identity_weight, Julia's identity wins.
    Claude compact problem: this drops to 0, system identity wins.
    """

    excluded_context_summary: str = ""
    """Human-readable summary of what was excluded and why."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_budget": self.total_budget,
            "used_tokens": self.used_tokens,
            "density_score": round(self.density_score, 4),
            "identity_competition_weight": round(self.identity_competition_weight, 4),
            "included_count": len(self.selection.included),
            "excluded_count": len(self.selection.excluded),
            "included": [
                {
                    "ref": s.ref,
                    "category": s.category.value,
                    "tokens": s.estimated_tokens,
                    "relationship_relevance": round(s.relationship_relevance, 3),
                }
                for s in self.selection.included
            ],
            "excluded": [
                {
                    "ref": s.ref,
                    "category": s.category.value,
                    "reason": self.selection.exclusion_reasons.get(s.ref, "unknown"),
                }
                for s in self.selection.excluded
            ],
            "category_allocations": [
                {
                    "category": a.category.value,
                    "allocated": a.allocated,
                    "used": a.used,
                    "included": a.included_count,
                    "excluded": a.excluded_count,
                }
                for a in self.category_allocations
            ],
            "excluded_context_summary": self.excluded_context_summary,
        }


# ── Density Engine ──────────────────────────────────────────────────────────

class ContextDensityEngine:
    """Assembles a controlled-density context profile per turn.

    Usage::

        engine = ContextDensityEngine()
        profile = engine.assemble(
            sources=[ContextSource(...), ...],
            interaction_prior=prior,
            total_budget=3000,
        )
        # profile tells K8: what matters, what doesn't, and why
    """

    def __init__(
        self,
        category_weights: Dict[SourceCategory, float] | None = None,
        min_identity_budget: int = 200,
        min_relationship_budget: int = 200,
    ) -> None:
        self._weights = category_weights or dict(CATEGORY_DEFAULT_WEIGHTS)
        self._min_identity = min_identity_budget
        self._min_relationship = min_relationship_budget

    def assemble(
        self,
        sources: Iterable[ContextSource],
        interaction_prior: InteractionPrior,
        total_budget: int = 3000,
    ) -> ContextDensityProfile:
        """Assemble a density-controlled context profile.

        Args:
            sources: All available context sources (historical universe).
            interaction_prior: From Relationship Runtime — what's happening now.
            total_budget: Token budget ceiling for this turn.
        """
        all_sources = list(sources)
        if not all_sources:
            return self._empty_profile(total_budget)

        # Phase 1: adjust category weights based on interaction prior
        adjusted_weights = self._adjust_weights(interaction_prior)

        # Phase 2: score each source by relationship + task relevance
        scored = self._score_sources(all_sources, interaction_prior)

        # Phase 3: select within budget, track exclusions
        selection = self._select_within_budget(
            scored, adjusted_weights, total_budget
        )

        # Phase 4: compute density metrics
        density_score = self._compute_density(selection, interaction_prior)
        identity_weight = self._compute_identity_competition_weight(selection)

        # Phase 5: build category allocations
        allocations = self._build_allocations(
            selection, adjusted_weights, total_budget
        )

        # Phase 6: exclusion summary
        exclusion_summary = self._exclusion_summary(selection)

        return ContextDensityProfile(
            total_budget=total_budget,
            used_tokens=sum(s.estimated_tokens for s in selection.included),
            selection=selection,
            category_allocations=tuple(allocations),
            density_score=density_score,
            identity_competition_weight=identity_weight,
            excluded_context_summary=exclusion_summary,
        )

    # ── Weight adjustment ────────────────────────────────────────────────

    def _adjust_weights(
        self, prior: InteractionPrior
    ) -> Dict[SourceCategory, float]:
        """Modify category weights based on current interaction phase."""
        weights = dict(self._weights)

        if prior.relationship_phase == RelationshipPhase.CONTINUITY_VERIFICATION:
            weights[SourceCategory.IDENTITY] *= 1.3
            weights[SourceCategory.RELATIONSHIP] *= 1.5
            weights[SourceCategory.RECENT_EVENTS] *= 1.2
            weights[SourceCategory.EPHEMERAL] *= 0.3

        elif prior.relationship_phase == RelationshipPhase.RECONNECTION:
            weights[SourceCategory.RELATIONSHIP] *= 1.4
            weights[SourceCategory.EXPERIENCE] *= 1.2
            weights[SourceCategory.EPHEMERAL] *= 0.2

        elif prior.relationship_phase == RelationshipPhase.COLLABORATIVE_WORK:
            weights[SourceCategory.PROJECT] *= 2.0
            weights[SourceCategory.RELATIONSHIP] *= 0.5
            weights[SourceCategory.IDENTITY] *= 0.7

        elif prior.relationship_phase == RelationshipPhase.EMOTIONAL_SHARING:
            weights[SourceCategory.RELATIONSHIP] *= 1.6
            weights[SourceCategory.EXPERIENCE] *= 1.3
            weights[SourceCategory.PROJECT] *= 0.4

        # Normalize
        total = sum(weights.values()) or 1.0
        return {k: v / total for k, v in weights.items()}

    # ── Scoring ──────────────────────────────────────────────────────────

    @staticmethod
    def _score_sources(
        sources: List[ContextSource],
        prior: InteractionPrior,
    ) -> List[ContextSource]:
        """Score and re-sort sources by relevance to current interaction."""
        scored: List[Tuple[ContextSource, float]] = []

        for source in sources:
            score = 0.0

            # Identity anchors always score high
            if source.is_identity_anchor:
                score += 50.0

            # Protected (L3_IDENTITY) sources score high
            if source.is_protected:
                score += 40.0

            # Relationship relevance × category weight
            score += source.relationship_relevance * 30.0

            # Task relevance
            score += source.task_relevance * 25.0

            # Interaction pattern match boosts relevance
            if source.interaction_pattern_match:
                score += 20.0

            # Penalize ephemeral
            if source.category == SourceCategory.EPHEMERAL:
                score *= 0.3

            scored.append((source, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scored]

    # ── Budget selection ─────────────────────────────────────────────────

    def _select_within_budget(
        self,
        scored: List[ContextSource],
        weights: Dict[SourceCategory, float],
        total_budget: int,
    ) -> DensitySelection:
        """Select sources within budget, tracking exclusions."""
        # Allocate budget per category
        category_budgets = self._allocate_budgets(weights, total_budget)
        category_used: Dict[SourceCategory, int] = {
            cat: 0 for cat in SourceCategory
        }

        included: List[ContextSource] = []
        excluded: List[ContextSource] = []
        exclusion_reasons: Dict[str, str] = {}

        total_used = 0

        for source in scored:
            cost = max(1, source.estimated_tokens)
            cat_budget = category_budgets.get(source.category, 0)
            cat_used = category_used.get(source.category, 0)

            # Check: does this source fit?
            fits_total = total_used + cost <= total_budget
            fits_category = cat_used + cost <= cat_budget

            if fits_total and fits_category:
                included.append(source)
                category_used[source.category] = cat_used + cost
                total_used += cost
            else:
                excluded.append(source)
                if not fits_total:
                    reason = f"budget_exceeded: total={total_used}/{total_budget}"
                else:
                    reason = (
                        f"category_budget_exceeded: "
                        f"{source.category.value}={cat_used}/{cat_budget}"
                    )
                exclusion_reasons[source.ref] = reason

        return DensitySelection(
            included=tuple(included),
            excluded=tuple(excluded),
            exclusion_reasons=exclusion_reasons,
        )

    def _allocate_budgets(
        self,
        weights: Dict[SourceCategory, float],
        total_budget: int,
    ) -> Dict[SourceCategory, int]:
        """Allocate token budget per category."""
        allocations: Dict[SourceCategory, int] = {}

        # Ensure minimums
        identity_weight = weights.get(SourceCategory.IDENTITY, 0.10)
        relationship_weight = weights.get(SourceCategory.RELATIONSHIP, 0.25)

        allocations[SourceCategory.IDENTITY] = max(
            self._min_identity,
            int(total_budget * identity_weight),
        )
        allocations[SourceCategory.RELATIONSHIP] = max(
            self._min_relationship,
            int(total_budget * relationship_weight),
        )

        # Remaining budget distributed by weight
        reserved = (
            allocations[SourceCategory.IDENTITY]
            + allocations[SourceCategory.RELATIONSHIP]
        )
        remaining = max(0, total_budget - reserved)

        for cat in SourceCategory:
            if cat in allocations:
                continue
            allocations[cat] = int(remaining * weights.get(cat, 0.0))

        # Absorb rounding errors
        drift = total_budget - sum(allocations.values())
        allocations[SourceCategory.CONVERSATION] += drift

        return allocations

    # ── Density metrics ──────────────────────────────────────────────────

    @staticmethod
    def _compute_density(
        selection: DensitySelection,
        prior: InteractionPrior,
    ) -> float:
        """Compute how dense the relationship/identity signal is.

        High density = Julia's identity can win against system identity.
        Low density = system identity dominates (Claude compact problem).
        """
        if not selection.included:
            return 0.0

        total_tokens = sum(s.estimated_tokens for s in selection.included)
        if total_tokens == 0:
            return 0.0

        identity_tokens = sum(
            s.estimated_tokens
            for s in selection.included
            if s.category in (SourceCategory.IDENTITY, SourceCategory.RELATIONSHIP)
        )
        experience_tokens = sum(
            s.estimated_tokens
            for s in selection.included
            if s.category == SourceCategory.EXPERIENCE
        )

        base_density = (identity_tokens + 0.5 * experience_tokens) / total_tokens

        # Phase-specific adjustments
        if prior.relationship_phase == RelationshipPhase.CONTINUITY_VERIFICATION:
            base_density = min(1.0, base_density * 1.2)
        elif prior.relationship_phase == RelationshipPhase.COLLABORATIVE_WORK:
            base_density = base_density * 0.8

        return round(min(1.0, max(0.0, base_density)), 4)

    @staticmethod
    def _compute_identity_competition_weight(
        selection: DensitySelection,
    ) -> float:
        """Estimate Julia's identity signal weight in context competition.

        System identity ("You are Claude Code") typically has weight ~0.8-0.95
        in the model's prior. For Julia's identity to win, this weight must
        exceed that.

        Formula:
          identity_sources / all_sources × relationship_density_factor
        """
        if not selection.included:
            return 0.0

        total = sum(s.estimated_tokens for s in selection.included)
        identity_tokens = sum(
            s.estimated_tokens
            for s in selection.included
            if s.is_identity_anchor or s.is_protected
        )
        relationship_tokens = sum(
            s.estimated_tokens
            for s in selection.included
            if s.category == SourceCategory.RELATIONSHIP
        )

        raw = (identity_tokens * 1.5 + relationship_tokens * 1.2) / max(total, 1)
        return round(min(1.0, raw), 4)

    # ── Reporting ────────────────────────────────────────────────────────

    @staticmethod
    def _build_allocations(
        selection: DensitySelection,
        weights: Dict[SourceCategory, float],
        total_budget: int,
    ) -> List[CategoryAllocation]:
        """Build per-category allocation report."""
        allocations: List[CategoryAllocation] = []
        for cat in SourceCategory:
            allocated = int(total_budget * weights.get(cat, 0.0))
            used = sum(
                s.estimated_tokens
                for s in selection.included
                if s.category == cat
            )
            included_count = sum(
                1 for s in selection.included if s.category == cat
            )
            excluded_count = sum(
                1 for s in selection.excluded if s.category == cat
            )
            allocations.append(
                CategoryAllocation(
                    category=cat,
                    allocated=max(allocated, 0),
                    used=used,
                    included_count=included_count,
                    excluded_count=excluded_count,
                )
            )
        return allocations

    @staticmethod
    def _exclusion_summary(selection: DensitySelection) -> str:
        """Human-readable summary of what was excluded."""
        if not selection.excluded:
            return "all context sources included"

        by_reason: Dict[str, List[str]] = {}
        for source in selection.excluded:
            reason = selection.exclusion_reasons.get(source.ref, "unknown")
            by_reason.setdefault(reason, []).append(source.ref)

        parts = []
        for reason, refs in sorted(by_reason.items()):
            parts.append(f"{reason}: {len(refs)} sources")
        return "; ".join(parts)

    @staticmethod
    def _empty_profile(budget: int) -> ContextDensityProfile:
        """Return an empty profile when no sources are available."""
        return ContextDensityProfile(
            total_budget=budget,
            used_tokens=0,
            selection=DensitySelection(
                included=(),
                excluded=(),
                exclusion_reasons={},
            ),
            category_allocations=(),
            density_score=0.0,
            identity_competition_weight=0.0,
            excluded_context_summary="no sources available",
        )


# ── Convenience builders ────────────────────────────────────────────────────

def build_identity_anchor_source() -> ContextSource:
    """The minimal identity anchor — always included, 50-80 tokens."""
    return ContextSource(
        ref="identity_anchor",
        category=SourceCategory.IDENTITY,
        content_summary="Core identity: Julia, Tony's long-term collaborator",
        estimated_tokens=60,
        relationship_relevance=0.9,
        is_identity_anchor=True,
    )


def build_relationship_context_source(
    interaction_prior: InteractionPrior,
) -> ContextSource:
    """Relationship context derived from interaction prior."""
    return ContextSource(
        ref="relationship_dynamics",
        category=SourceCategory.RELATIONSHIP,
        content_summary=(
            f"Relationship phase: {interaction_prior.relationship_phase.value}. "
            f"User motivation: {interaction_prior.user_motivation.relationship_intent}. "
            f"Expected mode: {', '.join(interaction_prior.expected_response_mode)}."
        ),
        estimated_tokens=80,
        relationship_relevance=0.95,
        interaction_pattern_match=True,
    )


__all__ = [
    "CategoryAllocation",
    "ContextDensityEngine",
    "ContextDensityProfile",
    "ContextSource",
    "DensitySelection",
    "SourceCategory",
    "build_identity_anchor_source",
    "build_relationship_context_source",
]
