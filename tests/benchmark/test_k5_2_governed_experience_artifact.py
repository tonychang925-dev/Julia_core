import json
import unittest
from pathlib import Path

from julia_core.experience import ExperienceArtifactBuilder, build_experience_context_block

OUTPUT = Path("artifacts/experience/julia_interaction_experience_v1.json")


class TestK52GovernedExperienceArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = ExperienceArtifactBuilder().write_artifact()
        cls.data = cls.artifact.to_dict()

    def test_artifact_written_and_versioned(self):
        self.assertTrue(OUTPUT.exists())
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(data["artifact_id"], "julia.interaction_experience")
        self.assertEqual(data["version"], "v1")
        self.assertEqual(data["source"]["authority"], "governed_experience")

    def test_required_dimensions_and_scores_exist(self):
        dims = self.data["experience_dimensions"]
        self.assertEqual(set(dims), {"identity_question", "relationship_boundary", "collaboration", "correction"})
        for dimension in dims.values():
            self.assertIn("trigger_patterns", dimension)
            self.assertIn("behavior_tendency", dimension)
            self.assertIn("preferred_response_mode", dimension["behavior_tendency"])
            self.assertIn("avoid_response_mode", dimension["behavior_tendency"])
            self.assertGreaterEqual(dimension["confidence"], 0.0)
        scores = self.data["scores"]
        self.assertEqual(scores["coverage_score"]["identity_question"], 1.0)
        self.assertIn("stability_score", scores)
        self.assertIn("transfer_score", scores)
        self.assertIn("interaction_coherence_density", scores)

    def test_governance_boundary(self):
        governance = self.data["governance"]
        self.assertFalse(governance["mutates_identity"])
        self.assertFalse(governance["mutates_persona"])
        self.assertFalse(governance["writes_memory"])
        self.assertFalse(governance["stores_raw_chat"])
        self.assertFalse(governance["stores_fixed_answer_templates"])
        self.assertFalse(governance["provider_reads_artifact_directly"])
        self.assertTrue(governance["requires_review"])

    def test_experience_context_block_interface(self):
        block = build_experience_context_block(self.artifact, "Tony 说我理解错了，正确答案是...")
        data = block.to_dict()
        self.assertEqual(data["context_type"], "interaction_experience")
        self.assertEqual(data["purpose"], "experience_aware_behavior_reconstruction")
        self.assertIn("correction", data["selected_dimensions"])
        self.assertTrue(data["behavior_guidance"])
        self.assertFalse(data["boundary"]["provider_reads_artifact_directly"])
        payload = json.dumps(data, ensure_ascii=False)
        self.assertNotIn("conversation", payload.lower())
        self.assertNotIn("answer_template", payload.lower())

    def test_artifact_contains_no_raw_chat_or_fixed_response_template(self):
        payload = json.dumps(self.data, ensure_ascii=False).lower()
        self.assertNotIn("full_conversation", payload)
        self.assertFalse(self.data["governance"]["stores_raw_chat"])
        self.assertFalse(self.data["governance"]["stores_fixed_answer_templates"])
        self.assertNotIn("answer y", payload)
        self.assertNotIn("when tony asks x", payload)


if __name__ == "__main__":
    unittest.main()
