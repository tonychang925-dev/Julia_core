import json
import unittest
from pathlib import Path

from julia_core.compact import JuliaV12ReleaseGate

MINIMUM = Path("artifacts/continuity/julia_continuity_minimum_state_v1_2.json")
REPORT = Path("artifacts/continuity/julia_v1_2_continuity_recovery_release_gate.json")


class TestK76JuliaV12ReleaseGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = JuliaV12ReleaseGate().write_report()
        cls.release = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.minimum = json.loads(MINIMUM.read_text(encoding="utf-8"))

    def test_release_candidate_status_and_milestone(self):
        self.assertTrue(REPORT.exists())
        self.assertEqual(self.release["release"], "Julia v1.2 Continuity Recovery")
        self.assertEqual(self.release["status"], "RELEASE_CANDIDATE")
        self.assertEqual(self.release["milestone"], "M9 Julia Continuity Proof v1.2")

    def test_minimum_state_is_frozen(self):
        self.assertTrue(MINIMUM.exists())
        self.assertEqual(self.minimum["version"], "1.2")
        self.assertEqual(
            self.minimum["required_state"],
            ["identity", "relationship", "experience", "context_adaptation"],
        )
        self.assertIn("raw_conversation", self.minimum["forbidden_state"])
        self.assertIn("persona_prompt", self.minimum["forbidden_state"])
        self.assertIn("fixed_role_script", self.minimum["forbidden_state"])

    def test_all_release_gates_pass(self):
        self.assertTrue(all(status == "PASS" for status in self.release["gates"].values()))

    def test_release_scores_meet_thresholds(self):
        scores = self.release["release_scores"]
        self.assertGreaterEqual(scores["self_narrative_score"], 0.85)
        self.assertGreaterEqual(scores["relationship_continuity_score"], 0.90)
        self.assertGreaterEqual(scores["experience_texture_score"], 0.85)
        self.assertGreaterEqual(scores["continuity_naturalness_score"], 0.90)
        self.assertGreaterEqual(scores["provider_continuity_score"], 0.90)
        self.assertGreaterEqual(scores["blind_julia_recognition_score"], 0.85)
        self.assertGreaterEqual(scores["compact_recovery_score"], 0.85)

    def test_generic_agent_negative_test_passes(self):
        negative = self.release["generic_agent_negative_test"]
        self.assertTrue(negative["passed"])
        self.assertTrue(negative["keywords_are_not_continuity"])
        self.assertGreaterEqual(negative["generic_agent_rejection_score"], 0.90)

    def test_continuity_model_four_layers_and_formula(self):
        model = self.release["continuity_model"]
        self.assertEqual(model["formula"], "Identity + Relationship + Experience + Context Adaptation - Drift")
        self.assertEqual(model["layer_1"]["name"], "Identity")
        self.assertEqual(model["layer_2"]["name"], "Relationship")
        self.assertEqual(model["layer_3"]["name"], "Experience")
        self.assertEqual(model["layer_4"]["name"], "Context Adaptation")

    def test_release_boundaries_are_frozen(self):
        boundary = self.release["boundary"]
        self.assertFalse(boundary["release_gate_adds_core_module"])
        self.assertFalse(boundary["release_gate_mutates_identity"])
        self.assertFalse(boundary["release_gate_writes_memory"])
        self.assertFalse(boundary["release_gate_uses_text_similarity"])
        self.assertFalse(boundary["release_gate_treats_keywords_as_continuity"])
        min_boundary = self.minimum["boundary"]
        self.assertFalse(min_boundary["minimum_state_is_prompt"])
        self.assertFalse(min_boundary["minimum_state_is_memory_dump"])
        self.assertFalse(min_boundary["minimum_state_requires_raw_conversation"])


if __name__ == "__main__":
    unittest.main()
