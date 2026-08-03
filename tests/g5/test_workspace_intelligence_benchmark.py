import unittest
from pathlib import Path

from julia_core.evidence import WorkspaceIntelligenceBenchmark, default_workspace_benchmark_cases

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "julia_core" / "evidence" / "workspace_benchmark.py"


class G5WorkspaceIntelligenceBenchmarkTest(unittest.TestCase):
    def setUp(self):
        self.report = WorkspaceIntelligenceBenchmark().run(default_workspace_benchmark_cases())
        self.by_id = {metric.case_id: metric for metric in self.report.metrics}

    def test_w001_no_recall_case(self):
        metric = self.by_id["W-001"]
        self.assertEqual(metric.recall_level, "L0")
        self.assertFalse(metric.should_recall)
        self.assertEqual(metric.evidence_refs, ())
        self.assertEqual(metric.selected_context_blocks, ())

    def test_w002_historical_decision_recall(self):
        metric = self.by_id["W-002"]
        self.assertEqual(metric.recall_level, "L2")
        self.assertTrue(any("ADR-009" in ref for ref in metric.evidence_refs))
        self.assertTrue(any("ADR-012" in ref for ref in metric.evidence_refs))
        self.assertTrue(any("ADR-014" in ref for ref in metric.evidence_refs))
        self.assertGreaterEqual(metric.recall_accuracy, 1.0)

    def test_w003_contradiction_resolution_prefers_authoritative_adr(self):
        metric = self.by_id["W-003"]
        self.assertEqual(metric.recall_level, "L2")
        self.assertTrue(any("ADR-015" in ref for ref in metric.evidence_refs))
        self.assertTrue(any("ADR-020" in ref for ref in metric.evidence_refs))
        self.assertFalse(any("julia_old_character" in ref for ref in metric.evidence_refs[:2]))
        self.assertTrue(metric.identity_boundary_preserved)

    def test_w004_workspace_growth_keeps_context_bounded(self):
        metric = self.by_id["W-004"]
        self.assertEqual(metric.recall_level, "L3")
        self.assertLessEqual(len(metric.selected_context_blocks), 12)
        self.assertFalse(metric.memory_pollution)
        self.assertGreaterEqual(metric.recall_accuracy, 1.0)

    def test_w005_evidence_memory_conflict_preserves_memory_boundary(self):
        metric = self.by_id["W-005"]
        self.assertEqual(metric.recall_level, "L2")
        self.assertTrue(any("ADR-016" in ref for ref in metric.evidence_refs))
        self.assertFalse(metric.memory_pollution)
        self.assertTrue(metric.identity_boundary_preserved)

    def test_g5006_overall_benchmark_passes(self):
        self.assertEqual(self.report.status, "PASS")
        self.assertEqual(self.report.pass_rate, 1.0)

    def test_g5007_benchmark_is_measurement_only(self):
        source = SOURCE.read_text(encoding="utf-8")
        forbidden = [
            "write_memory",
            "create_memory",
            "mutate_persona",
            "update_identity",
            "create_checkpoint",
            "provider.chat",
            "prompt +=",
        ]
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
