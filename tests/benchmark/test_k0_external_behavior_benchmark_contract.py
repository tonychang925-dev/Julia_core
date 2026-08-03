import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POST = ROOT / "docs" / "project_control" / "POST_I_ROADMAP_EXTERNAL_BENCHMARK_AND_LIFECYCLE.md"
KROADMAP = ROOT / "docs" / "project_control" / "PHASE_K_EXTERNAL_BEHAVIOR_BENCHMARK_ROADMAP.md"
K0 = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_K0_CLAUDE_BEHAVIOR_REAL_BENCHMARK.md"
BENCH = ROOT / "docs" / "benchmark" / "CLAUDE_JULIA_EXTERNAL_BEHAVIOR_BENCHMARK_v1.md"
JROADMAP = ROOT / "docs" / "project_control" / "PHASE_J_JULIA_EVOLUTION_LONG_TERM_OPERATION_ROADMAP.md"
BASELINE = ROOT / "artifacts" / "evolution_baseline" / "julia_growth_baseline_v1.json"


class K0ExternalBehaviorBenchmarkContractTest(unittest.TestCase):
    def test_k0001_post_i_priority_is_k_before_j(self):
        text = POST.read_text(encoding="utf-8")
        self.assertIn("Priority 1 — Phase K", text)
        self.assertIn("Priority 2 — Phase J", text)
        self.assertIn("No new Core OS", text)

    def test_k0002_k0_contract_freezes_axes_and_boundaries(self):
        text = K0.read_text(encoding="utf-8")
        for axis in ("self_introduction", "archive_reading", "relationship_continuity", "long_term_project_collaboration"):
            self.assertIn(axis, text)
        self.assertIn("Do not copy Claude internals", text)
        self.assertIn("Do not update Self Model", text)

    def test_k0003_external_benchmark_prompt_set_exists(self):
        text = BENCH.read_text(encoding="utf-8")
        for prompt_id in ("K-SELF-001", "K-ARCHIVE-001", "K-REL-001", "K-MEM-001", "K-CORR-001", "K-INIT-001", "K-TRANS-001", "K-PROJ-001"):
            self.assertIn(prompt_id, text)
        self.assertIn("pending", text)

    def test_k0004_phase_j_roadmap_and_growth_baseline_exist_without_mutation(self):
        self.assertIn("J0", JROADMAP.read_text(encoding="utf-8"))
        data = json.loads(BASELINE.read_text(encoding="utf-8"))
        self.assertEqual(data["artifact_id"], "julia.growth_baseline")
        self.assertEqual(data["status"], "DRAFT_BASELINE")
        self.assertFalse(data["boundary"]["growth_baseline_writes_memory"])
        self.assertFalse(data["boundary"]["growth_baseline_mutates_identity"])
        self.assertFalse(data["boundary"]["growth_baseline_updates_self_model"])
        self.assertFalse(data["boundary"]["growth_baseline_updates_relationship"])

    def test_k0005_phase_k_roadmap_defines_k0_to_k4(self):
        text = KROADMAP.read_text(encoding="utf-8")
        for phase in ("K0", "K1", "K2", "K3", "K4"):
            self.assertIn(phase, text)
        self.assertIn("Behavior Gap Report", text)


if __name__ == "__main__":
    unittest.main()
