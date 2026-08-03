import tempfile
import unittest
from pathlib import Path

from julia_core.evolution import EvolutionProposalJsonlStore, RealityFeedbackAnalyzer, adaptation_quality_score
from julia_core.observer import DailyRelationshipSnapshot

ROOT = Path(__file__).resolve().parents[2]
EVOLUTION_SOURCE = ROOT / "julia_core" / "evolution" / "proposals.py"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_H6_2_REALITY_FEEDBACK_ANALYSIS.md"
REPORT = ROOT / "docs" / "verification" / "H6_2_REALITY_FEEDBACK_ANALYSIS_REPORT_v1.md"
FEATURE = ROOT / "docs" / "project_control" / "FEATURE_SPEC_H6_2.md"
ROADMAP = ROOT / "docs" / "project_control" / "PHASE_H_JULIA_HUMAN_INTERFACE_LAYER_ROADMAP.md"


def snapshot(
    date,
    *,
    sessions=2,
    continuity=0.8,
    repeated=0.2,
    memory=0.5,
    evidence=0.8,
    corrections=2,
    friction=3,
    voice=0.1,
):
    return DailyRelationshipSnapshot(
        date=date,
        sessions=sessions,
        turns=sessions * 3,
        topics=("Julia Core",),
        continuity_success=continuity,
        repeated_explanation_rate=repeated,
        memory_usefulness=memory,
        evidence_success_rate=evidence,
        manual_corrections=corrections,
        human_friction_score=friction,
        voice_usage_ratio=voice,
    )


class H62RealityFeedbackAnalysisTest(unittest.TestCase):
    def test_h6201_repeated_friction_generates_context_improvement_proposal(self):
        analysis = RealityFeedbackAnalyzer().analyze([snapshot("2026-08-01"), snapshot("2026-08-02")])
        proposal_types = {proposal.type for proposal in analysis.proposals}
        self.assertIn("context_improvement", proposal_types)
        proposal = next(item for item in analysis.proposals if item.type == "context_improvement")
        self.assertEqual(proposal.target, "Context OS")
        self.assertTrue(proposal.requires_human_approval)
        self.assertFalse(proposal.boundary["proposal_is_memory"])
        self.assertFalse(proposal.boundary["proposal_auto_applied"])

    def test_h6202_user_habit_and_provider_limitation_are_classified_separately(self):
        analysis = RealityFeedbackAnalyzer().analyze(
            [
                snapshot("2026-08-01", continuity=0.95, repeated=0.0, friction=0, evidence=0.9, voice=0.0),
                snapshot("2026-08-02", continuity=0.95, repeated=0.0, friction=0, evidence=0.8, voice=0.1),
            ]
        )
        categories = {item.category for item in analysis.classifications}
        targets = {proposal.target for proposal in analysis.proposals}
        self.assertIn("user_habit", categories)
        self.assertIn("provider_limitation", categories)
        self.assertIn("Reality Baseline", targets)
        self.assertIn("Provider Boundary", targets)

    def test_h6203_ap001_single_event_overreaction_is_noise(self):
        analysis = RealityFeedbackAnalyzer().analyze([snapshot("2026-08-02", friction=9, repeated=1.0, continuity=0.0)])
        self.assertEqual(len(analysis.proposals), 0)
        self.assertEqual(analysis.classifications[0].category, "noise")
        self.assertEqual(analysis.classifications[0].target, "No Action")

    def test_h6204_proposal_store_is_append_only_artifact_not_memory(self):
        analysis = RealityFeedbackAnalyzer().analyze([snapshot("2026-08-01"), snapshot("2026-08-02")])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evolution_proposals.jsonl"
            stored = EvolutionProposalJsonlStore(path).append_many(analysis.proposals)
            self.assertEqual(len(stored), len(analysis.proposals))
            text = path.read_text(encoding="utf-8")
            self.assertIn("requires_human_approval", text)
            self.assertIn("proposal_auto_applied", text)
            self.assertNotIn("memory_ref", text)
            self.assertNotIn("identity_updated", text)

    def test_h6205_adaptation_quality_score_rewards_useful_governed_change(self):
        analysis = RealityFeedbackAnalyzer().analyze([snapshot("2026-08-01"), snapshot("2026-08-02")])
        self.assertGreaterEqual(adaptation_quality_score(analysis.proposals), 0.0)
        self.assertEqual(analysis.adaptation_quality_score, adaptation_quality_score(analysis.proposals))

    def test_h6206_ap002_ap003_forbidden_auto_evolution_tokens_absent(self):
        source = EVOLUTION_SOURCE.read_text(encoding="utf-8")
        forbidden = [
            "write_memory",
            "create_memory",
            "MemoryRef(",
            "mutate_persona",
            "update_identity",
            "auto_update_persona",
            "identity_updated",
            "persona_updated",
            "reduce_correction_by_silencing_confirmation",
        ]
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_h6207_contract_report_feature_and_roadmap_document_h62(self):
        self.assertIn("H6.2 — Reality Feedback Analysis", CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("Category A", CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("Anti-pattern", CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("H6.2 Reality Feedback Analysis", REPORT.read_text(encoding="utf-8"))
        self.assertIn("H6.2-T01", FEATURE.read_text(encoding="utf-8"))
        roadmap = ROADMAP.read_text(encoding="utf-8")
        self.assertIn("H6.2 | Reality Feedback Analysis ✅", roadmap)
        self.assertIn("H6.3 | Julia Assistant v1.0 Release", roadmap)


if __name__ == "__main__":
    unittest.main()
