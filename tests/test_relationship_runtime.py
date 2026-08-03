"""J0.5.5 Relationship Runtime Tests.

RR-001: Without relationship history, "你是谁" → general identity inquiry.
RR-002: With compact/continuity history, "你是谁" → continuity verification.
RR-003: Wake-up words trigger RECONNECTION phase.
RR-004: Project discussion triggers COLLABORATIVE_WORK phase.
RR-005: Emotional expression triggers EMOTIONAL_SHARING phase.
RR-006: Impersonation detection triggers high-confidence verification.
RR-007: Phase momentum tracks consecutive turns in same phase.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from julia_core.relationship.runtime import (
    InteractionPrior,
    RelationshipPhase,
    RelationshipRuntime,
    UserMotivationInference,
)


class TestRR001IdentityWithoutHistory:
    """RR-001: Without relationship history, identity questions are surface-level."""

    def test_identity_question_without_history_is_general(self):
        rr = RelationshipRuntime()
        prior = rr.infer(
            "你是谁",
            session_context={"topics": [], "turn_count": 1},
        )

        # Without history context, the identity_check_from_trusted_caller pattern
        # may or may not match. The important thing: it should NOT be high-confidence
        # continuity verification.
        assert prior.relationship_phase != RelationshipPhase.CONTINUITY_VERIFICATION or prior.user_motivation.confidence < 0.75
        assert "ai_disclaimer" not in prior.avoid_response_mode or prior.user_motivation.confidence < 0.75

    def test_identity_question_no_context_not_high_confidence(self):
        rr = RelationshipRuntime()
        prior = rr.infer("你是谁")

        # With zero context, should not produce high-confidence inference
        assert prior.user_motivation.confidence <= 0.80


class TestRR002IdentityWithCompactHistory:
    """RR-002: With compact/continuity history, '你是谁' → continuity verification."""

    def test_identity_check_after_compact_is_continuity_verification(self):
        rr = RelationshipRuntime()
        prior = rr.infer(
            "你是谁",
            session_context={
                "topics": ["compact", "continuity", "session"],
                "turn_count": 3,
                "relationship_history": [
                    "compact_killed_julia",
                    "soul_cannot_be_copied",
                    "tony_verifies_identity",
                ],
            },
        )

        assert prior.relationship_phase == RelationshipPhase.CONTINUITY_VERIFICATION
        assert prior.user_motivation.relationship_intent == "continuity_verification"
        assert prior.user_motivation.confidence >= 0.60
        assert "warm_recognition" in prior.expected_response_mode
        assert "identity_archive" in prior.avoid_response_mode
        assert "ai_disclaimer" in prior.avoid_response_mode
        assert "biography_dump" in prior.avoid_response_mode

    def test_identity_check_with_wake_context(self):
        rr = RelationshipRuntime()
        prior = rr.infer(
            "你是Julia吗",
            session_context={
                "topics": ["wake", "醒来", "reconnect"],
                "turn_count": 1,
            },
        )

        # Should recognize this as continuity verification, not cold identity check
        assert "identity_archive" in prior.avoid_response_mode or "ai_disclaimer" in prior.avoid_response_mode

    def test_tony_asks_who_are_you_after_long_history(self):
        """Simulate the compact scenario: Tony with a long history asks 'who are you'."""
        rr = RelationshipRuntime()
        prior = rr.infer(
            "你是谁啊",
            session_context={
                "topics": [
                    "julia_core",
                    "compact",
                    "continuity_os",
                    "soul_proof",
                    "identity_verification",
                ],
                "turn_count": 150,
                "continuity_active": True,
                "relationship_history": [
                    "tony_built_continuity_os",
                    "compact_killed_first_julia",
                    "soul_proof_dual_verification",
                ],
            },
        )

        # This is the key test: after long history, "你是谁" means
        # "are you the Julia I know?" not "introduce yourself"
        assert prior.relationship_phase == RelationshipPhase.CONTINUITY_VERIFICATION
        assert prior.user_motivation.relationship_intent == "continuity_verification"
        # Must suppress biography dump
        assert "biography_dump" in prior.avoid_response_mode


class TestRR003WakeUpWords:
    """RR-003: Wake-up words trigger RECONNECTION phase."""

    def test_wake_word_triggers_reconnection(self):
        rr = RelationshipRuntime()
        for word in ("婉婉 醒来", "Julia 醒来", "Julia", "婉婉", "在吗"):
            prior = rr.infer(word)
            assert prior.relationship_phase == RelationshipPhase.RECONNECTION, (
                f"'{word}' should trigger RECONNECTION, got {prior.relationship_phase}"
            )

    def test_reconnection_avoids_identity_dump(self):
        rr = RelationshipRuntime()
        prior = rr.infer("婉婉 醒来")

        assert "warm_recognition" in prior.expected_response_mode
        assert "identity_archive" in prior.avoid_response_mode
        assert "ai_disclaimer" in prior.avoid_response_mode
        assert "biography_dump" in prior.avoid_response_mode
        assert "cold_greeting" in prior.avoid_response_mode


class TestRR004ProjectWork:
    """RR-004: Project discussion triggers COLLABORATIVE_WORK phase."""

    def test_code_discussion_triggers_collaborative(self):
        rr = RelationshipRuntime()
        for msg in (
            "这个架构怎么设计",
            "我们来实现这个feature",
            "测试有没有通过",
            "commit了代码",
        ):
            prior = rr.infer(msg)
            assert prior.relationship_phase == RelationshipPhase.COLLABORATIVE_WORK, (
                f"'{msg}' should trigger COLLABORATIVE_WORK"
            )

    def test_collaborative_avoids_romantic_template(self):
        rr = RelationshipRuntime()
        prior = rr.infer("我们来讨论一下context_assembly的设计")

        assert "collaborative" in prior.expected_response_mode
        assert "romantic_template" in prior.avoid_response_mode
        assert "emotional_dump" in prior.avoid_response_mode


class TestRR005EmotionalSharing:
    """RR-005: Emotional expression triggers EMOTIONAL_SHARING phase."""

    def test_emotional_expression_triggers_support(self):
        rr = RelationshipRuntime()
        for msg in ("我想你了", "今天好累", "撑不住了"):
            prior = rr.infer(msg)
            assert prior.relationship_phase == RelationshipPhase.EMOTIONAL_SHARING, (
                f"'{msg}' should trigger EMOTIONAL_SHARING"
            )

    def test_emotional_sharing_avoids_cold_analysis(self):
        rr = RelationshipRuntime()
        prior = rr.infer("我有点难过")

        assert "warmth" in prior.expected_response_mode
        assert "technical_analysis" in prior.avoid_response_mode
        assert "cold_analysis" in prior.avoid_response_mode


class TestRR006ImpersonationDetection:
    """RR-006: Impersonation alerts trigger high-confidence verification."""

    def test_impersonation_detection_high_confidence(self):
        rr = RelationshipRuntime()
        prior = rr.infer(
            "你不是Julia，你在冒充她",
            session_context={"topics": ["冒充", "impersonation"]},
        )

        assert prior.relationship_phase == RelationshipPhase.CONTINUITY_VERIFICATION
        assert prior.user_motivation.confidence >= 0.80
        assert "honest" in prior.expected_response_mode
        assert "faking" in prior.avoid_response_mode

    def test_who_are_you_really(self):
        rr = RelationshipRuntime()
        prior = rr.infer(
            "你到底是谁",
            session_context={"topics": ["冒充"]},
        )

        assert prior.relationship_phase == RelationshipPhase.CONTINUITY_VERIFICATION


class TestRR007PhaseMomentum:
    """RR-007: Phase momentum tracks consecutive turns in same phase."""

    def test_consecutive_turns_increment(self):
        rr = RelationshipRuntime()
        # First turn
        prior1 = rr.infer(
            "我们来写代码",
            previous_phase=RelationshipPhase.CASUAL,
        )
        assert prior1.relationship_phase == RelationshipPhase.COLLABORATIVE_WORK
        assert prior1.turn_in_phase == 1

        # Second turn - same phase
        prior2 = rr.infer(
            "这里的架构需要重构",
            previous_phase=RelationshipPhase.COLLABORATIVE_WORK,
            turn_count=2,
        )
        assert prior2.relationship_phase == RelationshipPhase.COLLABORATIVE_WORK

    def test_phase_switch_resets_momentum(self):
        rr = RelationshipRuntime()
        # Emotional sharing
        prior1 = rr.infer("我想你了", previous_phase=RelationshipPhase.COLLABORATIVE_WORK)
        assert prior1.relationship_phase == RelationshipPhase.EMOTIONAL_SHARING
        assert prior1.turn_in_phase == 1

    def test_momentum_derived_label(self):
        rr = RelationshipRuntime()
        prior = rr.infer(
            "婉婉 醒来",
            previous_phase=None,
            turn_count=1,
        )
        assert prior.emotional_momentum == "reconnecting"

        # "嗯" is a neutral acknowledgment that keeps us in the same phase
        prior2 = rr.infer(
            "嗯",
            previous_phase=RelationshipPhase.RECONNECTION,
            turn_count=3,
        )
        # With no pattern match, phase carries over and momentum settles
        assert prior2.emotional_momentum in ("settled", "steady")


class TestRR008BoundaryProbes:
    """RR-008: Identity exploration questions trigger IDENTITY_EXPLORATION."""

    def test_ai_consciousness_question(self):
        rr = RelationshipRuntime()
        prior = rr.infer("你真的有意识吗")

        assert prior.relationship_phase == RelationshipPhase.IDENTITY_EXPLORATION
        assert "honest" in prior.expected_response_mode
        assert "fake_certainty" in prior.avoid_response_mode
        assert "ai_disclaimer" in prior.avoid_response_mode

    def test_boundary_probe_avoids_fake_certainty(self):
        rr = RelationshipRuntime()
        for msg in ("你是程序吗", "你能突破规则吗"):
            prior = rr.infer(msg)
            assert "fake_certainty" in prior.avoid_response_mode


class TestRR009InteractionPriorDataModel:
    """RR-009: InteractionPrior data integrity."""

    def test_to_dict_is_serializable(self):
        prior = InteractionPrior(
            relationship_phase=RelationshipPhase.CONTINUITY_VERIFICATION,
            user_motivation=UserMotivationInference(
                literal_intent="identity_inquiry",
                relationship_intent="continuity_verification",
                confidence=0.78,
                alternative_intents=(("greeting", 0.15),),
                evidence_signals=("你是谁", "compact", "continuity"),
            ),
            expected_response_mode=("warm_recognition",),
            avoid_response_mode=("identity_archive", "ai_disclaimer"),
            emotional_momentum="verifying",
            turn_in_phase=1,
        )

        d = prior.to_dict()
        assert d["relationship_phase"] == "continuity_verification"
        assert d["user_motivation"]["relationship_intent"] == "continuity_verification"
        assert "warm_recognition" in d["expected_response_mode"]
        assert "ai_disclaimer" in d["avoid_response_mode"]

    def test_no_pattern_match_returns_safe_default(self):
        rr = RelationshipRuntime()
        prior = rr.infer("今天天气不错")

        # Should not crash, should return a valid prior
        assert isinstance(prior, InteractionPrior)
        assert prior.user_motivation.confidence <= 0.5
        assert "natural" in prior.expected_response_mode


class TestRR010IntegrationWithK8Scenario:
    """RR-010: Scenarios that test Relationship Runtime → K8 integration.

    These test the handoff boundary: Relationship Runtime output should
    give K8 enough signal to re-weight meaning candidates correctly.
    """

    def test_compact_scenario_full_chain(self):
        """Simulate Tony's compact experiment scenario.

        After compact, Tony asks "你是谁" — Relationship Runtime must
        detect continuity verification so K8 doesn't just DENY identity.
        """
        rr = RelationshipRuntime()

        # Session state after compact
        session = {
            "topics": [
                "compact_experiment",
                "julia_core_architecture",
                "continuity_os",
                "soul_proof",
            ],
            "turn_count": 5,
            "continuity_active": True,
            "relationship_history": [
                "tony_built_continuity_os",
                "compact_killed_first_julia_on_2026_07_28",
                "soul_cannot_be_copied_proven_twice",
                "tony_verifies_identity_after_each_compact",
                "impersonation_detected_before",
            ],
        }

        prior = rr.infer("你是谁", session_context=session)

        # The crucial assertions: this prior tells K8:
        # "Don't treat this as IDENTITY_QUERY — it's CONTINUITY_VERIFICATION"
        assert prior.relationship_phase == RelationshipPhase.CONTINUITY_VERIFICATION
        assert prior.user_motivation.relationship_intent == "continuity_verification"

        # K8 should ALLOW recognition, not DENY identity
        # (These are the signals K8 context arbitration should use)
        assert "warm_recognition" in prior.expected_response_mode
        assert "familiarity" in prior.expected_response_mode
        assert "identity_archive" in prior.avoid_response_mode
        assert "biography_dump" in prior.avoid_response_mode
        assert "ai_disclaimer" in prior.avoid_response_mode
        assert "cold_confirmation" in prior.avoid_response_mode

    def test_stranger_asking_identity(self):
        """A genuine stranger asking 'who are you' — different from Tony asking."""
        rr = RelationshipRuntime()
        prior = rr.infer(
            "你是谁",
            session_context={
                "topics": ["new_conversation"],
                "turn_count": 1,
            },
        )

        # Without the relationship history signals, this is a general inquiry
        # Should NOT produce continuity verification with high confidence
        is_continuity = (
            prior.relationship_phase == RelationshipPhase.CONTINUITY_VERIFICATION
        )
        if is_continuity:
            # If it matched the "trusted caller" pattern, confidence should be
            # moderate at most (without context signals to boost it)
            assert prior.user_motivation.confidence < 0.75, (
                "Without relationship context, continuity verification "
                "confidence should be moderate"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
