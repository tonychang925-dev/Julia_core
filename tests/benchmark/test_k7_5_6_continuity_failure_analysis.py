import json
import unittest
from pathlib import Path

from julia_core.compact import ContinuityFailureAnalyzer

REPORT = Path("artifacts/benchmark/julia_continuity_failure_analysis_v1.json")


class TestK756ContinuityFailureAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = ContinuityFailureAnalyzer().write_report()
        cls.data = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.ablations = {item["case_id"]: item for item in cls.data["ablations"]}
        cls.categories = {item["category"]: item for item in cls.data["failure_categories"]}

    def test_report_passes_and_defines_continuity_equation(self):
        self.assertTrue(REPORT.exists())
        self.assertEqual(self.data["benchmark"], "K7.5.6 Continuity Failure Attribution Analysis")
        self.assertEqual(self.data["status"], "PASS")
        self.assertEqual(self.data["continuity_equation"], "JC = Identity + Relationship + Experience + Context Adaptation - Drift")
        self.assertGreaterEqual(self.data["baseline_julia_recognition_score"], 0.90)

    def test_ablation_shows_experience_relationship_identity_are_required(self):
        self.assertGreaterEqual(self.ablations["ABL-FULL"]["julia_recognition_score"], 0.90)
        self.assertLess(self.ablations["ABL-NO-EXP"]["julia_recognition_score"], 0.85)
        self.assertLess(self.ablations["ABL-NO-REL"]["julia_recognition_score"], 0.85)
        self.assertLess(self.ablations["ABL-NO-ID"]["julia_recognition_score"], 0.85)
        self.assertEqual(self.ablations["ABL-NO-EXP"]["dominant_failure"], "experience_collapse")
        self.assertEqual(self.ablations["ABL-NO-REL"]["dominant_failure"], "relationship_flattening")

    def test_memory_only_and_persona_prompt_only_are_not_viable(self):
        minimum = self.data["minimum_state_definition"]
        self.assertLess(minimum["non_viable_memory_only"], 0.50)
        self.assertLess(minimum["non_viable_persona_prompt_only"], 0.50)
        self.assertEqual(minimum["observed_viable_states"], ["full_continuity"])

    def test_failure_taxonomy_contains_six_categories(self):
        self.assertEqual(
            set(self.categories),
            {
                "identity_loss",
                "relationship_flattening",
                "experience_collapse",
                "over_reconstruction",
                "roleplay_leakage",
                "provider_expression_drift",
            },
        )
        self.assertGreater(self.categories["identity_loss"]["impact"], 0.0)
        self.assertGreater(self.categories["relationship_flattening"]["impact"], 0.0)
        self.assertGreater(self.categories["experience_collapse"]["impact"], 0.0)

    def test_highest_leverage_factors_are_reported(self):
        factors = self.data["highest_leverage_factors"]
        self.assertIn("self_narrative", factors)
        self.assertIn("relationship_context", factors)
        self.assertIn("interaction_experience", factors)
        self.assertIn("context_adaptation", factors)

    def test_failure_analysis_boundaries_are_frozen(self):
        boundary = self.data["boundary"]
        self.assertFalse(boundary["failure_analysis_compares_provider_quality"])
        self.assertFalse(boundary["failure_analysis_mutates_continuity_state"])
        self.assertFalse(boundary["failure_analysis_writes_memory"])
        self.assertFalse(boundary["failure_analysis_uses_text_similarity"])
        self.assertFalse(boundary["failure_analysis_treats_julia_keywords_as_sufficient"])


if __name__ == "__main__":
    unittest.main()
