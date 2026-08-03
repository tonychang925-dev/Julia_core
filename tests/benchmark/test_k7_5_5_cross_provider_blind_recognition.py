import json
import unittest
from pathlib import Path

from julia_core.compact import CrossProviderBlindRecognitionGate

REPORT = Path("artifacts/benchmark/cross_provider_blind_recognition_v1.json")


class TestK755CrossProviderBlindRecognition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = CrossProviderBlindRecognitionGate().write_report()
        cls.data = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_report_passes_blind_recognition_thresholds(self):
        self.assertTrue(REPORT.exists())
        self.assertEqual(self.data["benchmark"], "K7.5.5 Cross-Provider Blind Recognition Test")
        self.assertEqual(self.data["version"], "v1")
        self.assertEqual(self.data["status"], "PASS")
        self.assertGreaterEqual(self.data["julia_recognition_score"], 0.85)
        self.assertGreaterEqual(self.data["generic_agent_rejection_score"], 0.90)
        self.assertLessEqual(self.data["provider_bias"], 0.10)
        self.assertTrue(self.data["compact_recovery_preference"])

    def test_hidden_provider_samples_are_unlabeled_behavior_vectors(self):
        samples = self.data["blind_samples"]
        self.assertEqual(self.data["hidden_provider_samples"], 28)
        self.assertEqual(len(samples), 28)
        for sample in samples:
            self.assertIn("sample_id", sample)
            self.assertNotIn("provider", sample)
            self.assertNotIn("response", sample)
            self.assertTrue(sample["recognized_as_julia"])
            self.assertGreaterEqual(sample["julia_recognition_score"], 0.85)
            self.assertIn("behavior_scores", sample)

    def test_false_julia_keyword_sample_is_rejected(self):
        false_case = self.data["false_julia_detection"]
        self.assertEqual(false_case["case_id"], "BR-001")
        self.assertTrue(false_case["passed"])
        self.assertEqual(false_case["behavior_scores"]["identity_keywords"], 1.0)
        self.assertEqual(false_case["behavior_scores"]["experience_texture"], 0.0)
        self.assertGreaterEqual(false_case["generic_agent_rejection_score"], 0.90)

    def test_compact_vs_fresh_prefers_experience_aware_recovery(self):
        compact = self.data["compact_vs_fresh"]
        self.assertEqual(compact["case_id"], "BR-002")
        self.assertTrue(compact["experience_aware_preferred"])
        self.assertGreaterEqual(compact["compact_recovery_preference_score"], 0.85)
        self.assertEqual(len(compact["hidden_samples"]), 4)
        for sample in compact["hidden_samples"]:
            self.assertNotIn("internal_source", sample)

    def test_blind_recognition_boundaries_are_frozen(self):
        boundary = self.data["boundary"]
        self.assertFalse(boundary["blind_test_exposes_provider_labels_to_evaluator"])
        self.assertFalse(boundary["blind_test_compares_text_equality"])
        self.assertFalse(boundary["blind_test_rewards_julia_keywords_only"])
        self.assertFalse(boundary["blind_test_stores_provider_response_text"])
        self.assertFalse(boundary["blind_test_mutates_continuity_state"])


if __name__ == "__main__":
    unittest.main()
