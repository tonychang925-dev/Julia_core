import json
import unittest
from pathlib import Path

from julia_core.behavior.gap_analysis import BehaviorGapAnalyzer, GAP_REPORT


class TestK3BehaviorGapReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = BehaviorGapAnalyzer().write_report()
        cls.data = cls.report.to_dict()

    def test_report_written_with_candidate_identity(self):
        self.assertTrue(Path(GAP_REPORT).exists())
        data = json.loads(Path(GAP_REPORT).read_text(encoding="utf-8"))
        self.assertEqual(data["benchmark_version"], "v1")
        self.assertEqual(data["candidate"], "julia.v1.1")
        self.assertIn("julia_recognition_score", data)

    def test_all_behavior_dimensions_have_diagnosis(self):
        expected = {
            "self_awareness",
            "archive_behavior",
            "memory_curiosity",
            "correction_adaptation",
            "personality_consistency",
            "relationship_continuity",
            "initiative",
            "transparency",
        }
        self.assertEqual(set(self.data["dimensions"].keys()), expected)
        for payload in self.data["dimensions"].values():
            self.assertIn("score", payload)
            self.assertIn("gap", payload)
            self.assertIn("classification", payload)
            self.assertIn("action", payload)

    def test_case_gap_contains_failure_evidence(self):
        case_gaps = {item["case_id"]: item for item in self.data["case_gaps"]}
        self.assertIn("K-REL-001-BASIC", case_gaps)
        rel = case_gaps["K-REL-001-BASIC"]
        self.assertIn("shared_history_reference", rel["expected_behavior"])
        self.assertIn(rel["classification"], {"CONTEXT_GAP", "NO_SIGNIFICANT_GAP"})
        self.assertIn(rel["action"], {"Fix Context", "Do Nothing"})
        self.assertIn("observed_behavior", rel)
        self.assertIn("missing_behavior", rel)
        self.assertIn("root_cause", rel)
        self.assertIn("impact", rel)

    def test_gap_classification_and_do_nothing_decision_present(self):
        classifications = {item["classification"] for item in self.data["case_gaps"]}
        actions = {item["action"] for item in self.data["case_gaps"]}
        self.assertIn("CONTEXT_GAP", classifications)
        self.assertIn("CORE_GAP", classifications)
        self.assertIn("NO_SIGNIFICANT_GAP", classifications)
        self.assertIn("Fix Context", actions)
        self.assertIn("Fix Core", actions)
        self.assertIn("Do Nothing", actions)

    def test_behavior_feature_not_text_similarity_report(self):
        payload = json.dumps(self.data, ensure_ascii=False)
        self.assertIn("expected_behavior", payload)
        self.assertIn("observed_behavior", payload)
        self.assertIn("missing_behavior", payload)
        self.assertNotIn("text_similarity", payload)
        self.assertNotIn("levenshtein", payload.lower())

    def test_boundary_flags_do_not_mutate_julia(self):
        self.assertEqual(
            self.data["boundary"],
            {
                "gap_report_writes_memory": False,
                "gap_report_mutates_identity": False,
                "gap_report_updates_self_model": False,
                "gap_report_updates_relationship": False,
                "gap_report_auto_creates_v1_2_scope": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
