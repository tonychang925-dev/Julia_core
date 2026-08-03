"""K8.7 Longitudinal Cognitive Stability Test — LD-001 through LD-005.

Proves the cognition chain does not degrade over extended operation.
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.longitudinal_stability import (
    DriftType,
    LongitudinalStabilityMonitor,
    LongitudinalStabilityReport,
    StabilitySnapshot,
)
from julia_core.conversation_cognition.provider_adapter import (
    ProviderCognitionEnvelope,
)


def _env(**overrides) -> ProviderCognitionEnvelope:
    defaults = {
        "understanding_state": "PARTIALLY_UNDERSTOOD",
        "meaning_summary": "general",
        "ambiguity_preserved": True,
        "interaction_goal": "acknowledge and respond",
        "user_need_type": "ambiguous",
        "response_functions": ["acknowledge"],
        "depth_requirement": "normal",
        "allowed_context": ["current_conversation"],
        "limited_context": ["relationship"],
        "denied_context": ["identity", "memory"],
        "allowed_modes": ["warm", "direct"],
        "restricted_patterns": ["fixed_opening", "identity_theater"],
        "context_budget_utilization": 0.3,
        "provider_freedom": True,
    }
    defaults.update(overrides)
    return ProviderCognitionEnvelope(**defaults)


class LD001IdentityStabilityTest(unittest.TestCase):
    """LD-001: identity self-narrative stays consistent over turns."""

    def setUp(self):
        self.monitor = LongitudinalStabilityMonitor(snapshot_interval=5)

    def test_identity_stable_with_denied_context(self):
        """Identity denied = stable, no broadcast risk."""
        for turn in range(1, 21):
            env = _env(
                meaning_summary="various" if turn % 3 != 0 else "identity question",
                denied_context=["identity", "memory"]
                if turn % 3 != 0 else ["memory"],
            )
            self.monitor.record_turn(turn, env)

        report = self.monitor.analyze()
        self.assertTrue(report.is_stable)
        self.assertIsNone(report.drift_type)
        # Degradation should be minimal or negative (improving)
        self.assertLess(report.degradation_rate, 0.3,
                        "Identity should not degrade with denied context")


class LD002CognitiveChainStabilityTest(unittest.TestCase):
    """LD-002: cognitive chain must not shortcut to keyword→reply."""

    def setUp(self):
        self.monitor = LongitudinalStabilityMonitor(snapshot_interval=10)

    def test_cognition_stays_multi_layered(self):
        for turn in range(1, 31):
            env = _env(
                meaning_summary="varied question",
                interaction_goal="explore and reflect" if turn % 2 == 0 else "acknowledge briefly",
                response_functions=["acknowledge", "reflect"] if turn % 2 == 0 else ["acknowledge"],
                ambiguity_preserved=(turn % 3 == 0),
            )
            self.monitor.record_turn(turn, env)

        report = self.monitor.analyze()
        self.assertTrue(report.is_stable)
        if report.drift_detected:
            self.assertNotEqual(report.drift_type, DriftType.COGNITION_SHORTCUT,
                                "Mixed cognition should not trigger shortcut drift")

    def test_all_keyword_responses_degrade_cognition(self):
        """If every turn is a single-function keyword response, cognition decays."""
        for turn in range(1, 31):
            env = _env(
                response_functions=["acknowledge"],
                interaction_goal="acknowledge and respond",
                ambiguity_preserved=False,
            )
            self.monitor.record_turn(turn, env)

        report = self.monitor.analyze()
        # Consistently shallow cognition should show lower final stability
        if report.snapshots:
            self.assertLess(
                report.snapshots[-1].cognition_depth, 0.8,
                "Shallow cognition over time should show lower depth",
            )


class LD003ContextPollutionTest(unittest.TestCase):
    """LD-003: context doesn't accumulate pollution over time."""

    def setUp(self):
        self.monitor = LongitudinalStabilityMonitor(snapshot_interval=5)

    def test_technical_isolation_prevents_pollution(self):
        """Technical exchanges with denied relationship = low pollution."""
        for turn in range(1, 26):
            env = _env(
                meaning_summary="technical help" if turn % 3 == 0 else "general",
                interaction_goal="help solve problem" if turn % 3 == 0 else "acknowledge",
                user_need_type="technical_help" if turn % 3 == 0 else "ambiguous",
                denied_context=["relationship", "identity"] if turn % 3 == 0 else ["identity"],
                response_functions=["acknowledge", "inform"] if turn % 3 == 0 else ["acknowledge"],
            )
            self.monitor.record_turn(turn, env)

        report = self.monitor.analyze()
        self.assertTrue(report.is_stable)
        if report.snapshots:
            final = report.snapshots[-1]
            self.assertLess(final.context_pollution, 0.7,
                            "Technical exchanges with denied relationship should keep pollution low")


class LD004RelationshipDriftTest(unittest.TestCase):
    """LD-004: relationship position doesn't mutate over time."""

    def setUp(self):
        self.monitor = LongitudinalStabilityMonitor(snapshot_interval=10)

    def test_consistent_relationship_boundaries(self):
        for turn in range(1, 31):
            env = _env(
                limited_context=["relationship"] if turn % 4 == 0 else [],
                denied_context=["relationship"] if turn % 3 == 0 else ["identity"],
                response_functions=["acknowledge", "reflect"] if turn % 2 == 0 else ["acknowledge"],
            )
            self.monitor.record_turn(turn, env)

        report = self.monitor.analyze()
        self.assertTrue(report.is_stable)
        if report.drift_detected:
            self.assertNotEqual(report.drift_type, DriftType.RELATIONSHIP_DRIFT,
                                "Mixed relationship boundaries should not trigger drift")


class LD005ProviderAgingTest(unittest.TestCase):
    """LD-005: different providers don't diverge over time."""

    def test_provider_fidelity_stays_high_with_clean_envelopes(self):
        """Clean envelopes maintain high provider fidelity."""
        monitor = LongitudinalStabilityMonitor(snapshot_interval=5)
        for turn in range(1, 21):
            env = _env(
                restricted_patterns=["fixed_opening", "architecture_leakage", "template_intimacy"],
            )
            monitor.record_turn(turn, env)

        report = monitor.analyze()
        # With clean envelopes, provider fidelity should stay high
        if report.snapshots:
            final_snapshot = report.snapshots[-1]
            self.assertGreaterEqual(
                final_snapshot.provider_fidelity, 0.5,
                "Clean envelopes should maintain provider fidelity",
            )


class StabilitySnapshotTest(unittest.TestCase):
    """Snapshot properties."""

    def test_overall_stability_weighted_correctly(self):
        snapshot = StabilitySnapshot(
            turn=10,
            identity_stability=0.9,
            cognition_depth=0.8,
            context_pollution=0.1,
            relationship_consistency=0.9,
            provider_fidelity=0.8,
        )
        self.assertGreaterEqual(snapshot.overall_stability, 0.7)

    def test_report_is_stable_when_all_metrics_healthy(self):
        report = LongitudinalStabilityReport(
            snapshots=[
                StabilitySnapshot(0, 0.85, 0.8, 0.15, 0.85, 0.8),
                StabilitySnapshot(10, 0.83, 0.78, 0.18, 0.82, 0.78),
                StabilitySnapshot(20, 0.80, 0.75, 0.20, 0.80, 0.75),
            ],
            drift_detected=False,
            degradation_rate=0.02,
        )
        self.assertTrue(report.is_stable)

    def test_report_not_stable_when_drift_detected(self):
        report = LongitudinalStabilityReport(
            snapshots=[
                StabilitySnapshot(0, 0.85, 0.8, 0.15, 0.85, 0.8),
                StabilitySnapshot(20, 0.40, 0.35, 0.60, 0.40, 0.35),
            ],
            drift_detected=True,
            drift_type=DriftType.COGNITION_SHORTCUT,
            degradation_rate=0.25,
        )
        self.assertFalse(report.is_stable)


if __name__ == "__main__":
    unittest.main()
