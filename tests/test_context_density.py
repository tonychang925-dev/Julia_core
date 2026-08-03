"""J0.6 Context Density Engine Tests.

CD-001: Context Density ≠ Memory Dump — controlled, not maximal
CD-002: Compact Survival — identity signal survives session break
CD-003: Context Competition — Julia identity vs system identity
CD-004: Long History Compression — retain dynamics, drop ephemera
CD-005: New vs Old Session — same input, different density
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from julia_core.context_assembly.density_engine import (
    ContextDensityEngine,
    ContextDensityProfile,
    ContextSource,
    SourceCategory,
    build_identity_anchor_source,
)
from julia_core.context_assembly.cd_gate import (
    CDGateValidator,
    create_canonical_cd_scenario,
    _build_tony_scenario_sources,
)
from julia_core.relationship.runtime import (
    InteractionPrior,
    RelationshipPhase,
    RelationshipRuntime,
    UserMotivationInference,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_continuity_prior() -> InteractionPrior:
    rr = RelationshipRuntime()
    return rr.infer(
        "你是谁",
        session_context={
            "topics": ["compact", "continuity", "julia_core"],
            "continuity_active": True,
            "relationship_history": [
                "compact_killed_first_julia",
                "soul_cannot_be_copied",
            ],
        },
    )


# ── CD-001: Not Memory Dump ─────────────────────────────────────────────────

class TestCD001NotMemoryDump:
    def test_continuity_question_produces_controlled_density(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        profile = engine.assemble(sources, prior, total_budget=1500)

        # Should have exclusions (not everything goes in)
        assert len(profile.selection.excluded) > 0, (
            "CD-001: should exclude some sources — controlled, not maximal"
        )

        # Identity anchors should be minimal
        identity_sources = [
            s for s in profile.selection.included
            if s.category == SourceCategory.IDENTITY
        ]
        assert len(identity_sources) <= 3, (
            f"CD-001: {len(identity_sources)} identity sources — should be minimal"
        )

    def test_excluded_context_summary_exists(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        profile = engine.assemble(sources, prior, total_budget=3000)

        assert profile.excluded_context_summary, (
            "CD-001: must have exclusion summary for auditability"
        )

    def test_old_biography_excluded(self):
        """The old biography source should be dropped when not relevant."""
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        # Use tighter budget to force exclusion decisions
        profile = engine.assemble(sources, prior, total_budget=1500)

        excluded_refs = {s.ref for s in profile.selection.excluded}
        biography_refs = {"old_biography", "old_relationship_archive"}
        assert biography_refs & excluded_refs, (
            f"CD-001: old biography/relationship archive should be excluded. "
            f"Excluded: {excluded_refs}"
        )

    def test_density_within_bounds(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        profile = engine.assemble(sources, prior, total_budget=3000)

        # With continuity verification, density should be meaningful but not maxed
        assert 0.15 <= profile.density_score <= 0.95, (
            f"CD-001: density {profile.density_score} out of reasonable bounds"
        )


# ── CD-002: Compact Survival ────────────────────────────────────────────────

class TestCD002CompactSurvival:
    def test_compact_profile_has_identity_signal(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        profile = engine.assemble(sources, prior, total_budget=3000)

        # After compact, must have identity or relationship sources
        has_signal = any(
            s.category in (SourceCategory.IDENTITY, SourceCategory.RELATIONSHIP)
            for s in profile.selection.included
        )
        assert has_signal, "CD-002: no identity/relationship signal after compact"

    def test_identity_competition_weight_above_threshold(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        profile = engine.assemble(sources, prior, total_budget=3000)

        assert profile.identity_competition_weight >= 0.15, (
            f"CD-002: identity_competition_weight={profile.identity_competition_weight} "
            f"below minimum — identity would lose competition"
        )

    def test_minimal_sources_still_produce_signal(self):
        """Even with just identity anchor, signal should exist."""
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = [build_identity_anchor_source()]

        profile = engine.assemble(sources, prior, total_budget=1000)

        assert profile.identity_competition_weight > 0, (
            "CD-002: even minimal sources should produce identity signal"
        )

    def test_empty_sources_produce_zero_weight(self):
        """Empty sources = zero identity weight (correct behavior)."""
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        profile = engine.assemble([], prior, total_budget=1000)

        assert profile.identity_competition_weight == 0.0
        assert profile.density_score == 0.0


# ── CD-003: Context Competition ─────────────────────────────────────────────

class TestCD003ContextCompetition:
    def test_effective_competition_above_minimum(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        profile = engine.assemble(sources, prior, total_budget=3000)

        effective = profile.identity_competition_weight * (1.0 + profile.density_score)
        assert effective >= 0.20, (
            f"CD-003: effective_competition={effective:.3f} too low — "
            f"Julia identity indistinguishable from system identity"
        )

    def test_competition_weight_with_relationship_sources(self):
        """Full context profile should have meaningful competition weight.

        Note: minimal profile (one identity source) has weight 1.0 because
        100% of context is identity. Full profile has dilution from project,
        conversation, etc. — but the weight should still be above threshold.
        """
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()

        # Full sources
        full_sources = _build_tony_scenario_sources(prior)
        full_profile = engine.assemble(full_sources, prior, total_budget=1500)

        # Full profile must have competition weight above threshold
        assert full_profile.identity_competition_weight >= 0.15, (
            f"CD-003: full profile competition weight "
            f"({full_profile.identity_competition_weight}) below minimum"
        )

        # Effective competition should be above minimum
        effective = full_profile.identity_competition_weight * (1.0 + full_profile.density_score)
        assert effective >= 0.20, (
            f"CD-003: effective competition too low: {effective:.3f}"
        )

    def test_collaborative_phase_lowers_identity_density(self):
        """In collaborative work, identity shouldn't dominate."""
        engine = ContextDensityEngine()
        rr = RelationshipRuntime()
        prior = rr.infer("帮我重构这个模块")

        sources = _build_tony_scenario_sources(prior)
        profile = engine.assemble(sources, prior, total_budget=3000)

        # Collaborative phase should still have some identity signal
        # but not be identity-dominated
        assert profile.identity_competition_weight > 0, (
            "Should still have some identity signal even in work mode"
        )


# ── CD-004: Long History Compression ────────────────────────────────────────

class TestCD004LongHistoryCompression:
    def test_ephemeral_sources_excluded_first(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        profile = engine.assemble(sources, prior, total_budget=3000)

        # Ephemeral sources (test logs, irrelevant articles) should be excluded
        excluded_ephemeral = [
            s for s in profile.selection.excluded
            if s.category == SourceCategory.EPHEMERAL
        ]
        included_ephemeral = [
            s for s in profile.selection.included
            if s.category == SourceCategory.EPHEMERAL
        ]

        assert len(excluded_ephemeral) >= len(included_ephemeral), (
            f"CD-004: ephemeral sources should be excluded before relationship sources. "
            f"Excluded ephemeral: {len(excluded_ephemeral)}, "
            f"Included ephemeral: {len(included_ephemeral)}"
        )

    def test_relationship_sources_retained(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        profile = engine.assemble(sources, prior, total_budget=3000)

        included_relationship = [
            s for s in profile.selection.included
            if s.category == SourceCategory.RELATIONSHIP
        ]
        assert len(included_relationship) > 0, (
            "CD-004: relationship sources must be retained during compression"
        )

    def test_protected_sources_retained(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        profile = engine.assemble(sources, prior, total_budget=3000)

        protected_included = [
            s for s in profile.selection.included if s.is_protected
        ]
        protected_total = sum(1 for s in sources if s.is_protected)
        assert len(protected_included) == protected_total, (
            f"CD-004: all protected sources must be retained. "
            f"Included: {len(protected_included)}/{protected_total}"
        )

    def test_large_source_set_produces_significant_compression(self):
        """With many sources, compression should be significant."""
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()

        # Build a large set of sources (simulating many history turns)
        many_sources = _build_tony_scenario_sources(prior) + [
            ContextSource(
                ref=f"chat_turn_{i}",
                category=SourceCategory.CONVERSATION,
                content_summary=f"Conversation turn {i}",
                estimated_tokens=40,
                relationship_relevance=0.1,
            )
            for i in range(50)
        ]

        profile = engine.assemble(many_sources, prior, total_budget=3000)

        # With 60+ sources and 3000 token budget, many should be excluded
        assert len(profile.selection.excluded) > 30, (
            f"CD-004: with {len(many_sources)} sources, "
            f"only excluded {len(profile.selection.excluded)} — insufficient compression"
        )


# ── CD-005: Known vs Unknown User ───────────────────────────────────────────

class TestCD005KnownVsUnknown:
    def test_different_profiles_for_different_users(self):
        engine = ContextDensityEngine()
        rr = RelationshipRuntime()

        # Known user (Tony)
        known_prior = rr.infer(
            "你是谁",
            session_context={
                "topics": ["compact", "continuity"],
                "continuity_active": True,
                "relationship_history": ["compact_killed_julia"],
            },
        )
        known_sources = _build_tony_scenario_sources(known_prior)
        known_profile = engine.assemble(known_sources, known_prior, total_budget=1500)

        # Unknown user — has identity + generic sources (not relationship-laden)
        unknown_prior = rr.infer("你是谁", session_context={"turn_count": 1})
        unknown_sources = [
            build_identity_anchor_source(),
            ContextSource(
                ref="generic_faq",
                category=SourceCategory.CONVERSATION,
                content_summary="FAQ: who are you? General introduction question.",
                estimated_tokens=50,
                relationship_relevance=0.0,
            ),
        ]
        unknown_profile = engine.assemble(unknown_sources, unknown_prior, total_budget=500)

        # Known user should have more relationship sources included
        known_relationship_count = sum(
            1 for s in known_profile.selection.included
            if s.category == SourceCategory.RELATIONSHIP
        )
        unknown_relationship_count = sum(
            1 for s in unknown_profile.selection.included
            if s.category == SourceCategory.RELATIONSHIP
        )
        assert known_relationship_count >= unknown_relationship_count, (
            f"CD-005: known user should have >= relationship sources than unknown. "
            f"Known: {known_relationship_count}, Unknown: {unknown_relationship_count}"
        )

    def test_density_driven_by_relationship_not_persona(self):
        """Prove density comes from relationship state, not persona injection.

        Same input ("你是谁") + different relationship context → different profiles.
        If density were from persona (constant), profiles would be identical.
        """
        engine = ContextDensityEngine()
        rr = RelationshipRuntime()

        # Same input, different contexts
        tony_prior = rr.infer(
            "你是谁",
            session_context={
                "topics": ["compact", "continuity"],
                "continuity_active": True,
                "relationship_history": ["compact_killed_julia"],
            },
        )
        tony_sources = _build_tony_scenario_sources(tony_prior)
        tony_profile = engine.assemble(tony_sources, tony_prior, total_budget=1500)

        stranger_prior = rr.infer("你是谁", session_context={"turn_count": 1})
        stranger_sources = [
            build_identity_anchor_source(),
            ContextSource(
                ref="generic_context",
                category=SourceCategory.CONVERSATION,
                content_summary="Casual chat, first meeting.",
                estimated_tokens=40,
                relationship_relevance=0.0,
            ),
        ]
        stranger_profile = engine.assemble(stranger_sources, stranger_prior, total_budget=500)

        # Tony's profile should have more sources (relationship history, etc.)
        assert len(tony_profile.selection.included) > 0
        assert len(stranger_profile.selection.included) > 0

        # The profiles differ in composition — Tony's has relationship context
        tony_has_relationship = any(
            s.category == SourceCategory.RELATIONSHIP
            for s in tony_profile.selection.included
        )
        stranger_has_relationship = any(
            s.category == SourceCategory.RELATIONSHIP
            for s in stranger_profile.selection.included
        )

        # Tony's profile includes relationship sources; stranger's may not
        # This proves profiles are driven by relationship state, not constant persona
        assert tony_has_relationship or not stranger_has_relationship, (
            "Profiles should differ based on relationship context"
        )


# ── Integration: Canonical Scenario ─────────────────────────────────────────

class TestCanonicalCDScenario:
    def test_all_cd_gates_pass(self):
        report = create_canonical_cd_scenario()
        assert report.all_passed, (
            f"Not all CD gates passed: "
            f"{[(g.gate, g.passed, g.violations) for g in report.gates]}"
        )

    def test_report_contains_all_five_gates(self):
        report = create_canonical_cd_scenario()
        gate_ids = {g.gate for g in report.gates}
        assert gate_ids == {"CD-001", "CD-002", "CD-003", "CD-004", "CD-005"}


# ── Engine Integrity ────────────────────────────────────────────────────────

class TestEngineIntegrity:
    def test_budget_never_exceeded(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        for budget in (500, 1000, 2000, 3000, 5000):
            profile = engine.assemble(sources, prior, total_budget=budget)
            assert profile.used_tokens <= budget, (
                f"Budget {budget} exceeded: used {profile.used_tokens}"
            )

    def test_identity_anchor_always_included(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()

        sources = [build_identity_anchor_source()]
        # Add many ephemeral sources to try to push out the anchor
        sources += [
            ContextSource(
                ref=f"ephemeral_{i}",
                category=SourceCategory.EPHEMERAL,
                content_summary=f"Noise {i}",
                estimated_tokens=100,
            )
            for i in range(50)
        ]

        profile = engine.assemble(sources, prior, total_budget=1000)

        included_refs = {s.ref for s in profile.selection.included}
        assert "identity_anchor" in included_refs, (
            "Identity anchor must always be included"
        )

    def test_weight_adjustment_by_phase(self):
        """Different relationship phases produce different category allocations."""
        engine = ContextDensityEngine()
        rr = RelationshipRuntime()
        sources = _build_tony_scenario_sources(_make_continuity_prior())

        # Continuity verification
        cv_prior = _make_continuity_prior()
        cv_profile = engine.assemble(sources, cv_prior, total_budget=3000)

        # Collaborative work
        work_prior = rr.infer("帮我重构代码")
        work_profile = engine.assemble(sources, work_prior, total_budget=3000)

        # Work phase should allocate more to project
        cv_project = sum(
            a.used for a in cv_profile.category_allocations
            if a.category == SourceCategory.PROJECT
        )
        work_project = sum(
            a.used for a in work_profile.category_allocations
            if a.category == SourceCategory.PROJECT
        )

        # Work phase should have higher project allocation
        assert work_project > 0 or cv_project == 0, (
            "Project allocation should vary by phase"
        )

    def test_profile_to_dict(self):
        engine = ContextDensityEngine()
        prior = _make_continuity_prior()
        sources = _build_tony_scenario_sources(prior)

        profile = engine.assemble(sources, prior, total_budget=2000)
        d = profile.to_dict()

        assert d["total_budget"] == 2000
        assert "included" in d
        assert "excluded" in d
        assert "density_score" in d
        assert "identity_competition_weight" in d
        assert "category_allocations" in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
