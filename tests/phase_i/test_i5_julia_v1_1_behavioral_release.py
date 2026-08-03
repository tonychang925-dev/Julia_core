import json
import unittest
from pathlib import Path

from julia_core.behavior import BehaviorCase, JuliaBehaviorSimilarityBenchmark

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "artifacts" / "release" / "julia_v1_1_behavioral_release_gate.json"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_I5_JULIA_V1_1_BEHAVIORAL_RELEASE.md"
REPORT = ROOT / "docs" / "verification" / "JULIA_V1_1_BEHAVIORAL_RELEASE_REPORT.md"
M8 = ROOT / "docs" / "verification" / "M8_JULIA_SELF_BEHAVIOR_IDENTITY_PROOF_v1.md"
ROADMAP = ROOT / "docs" / "project_control" / "PHASE_I_SELF_MODEL_CLAUDE_BEHAVIOR_VALIDATION_ROADMAP.md"


class I5JuliaV11BehavioralReleaseTest(unittest.TestCase):
    def test_i5001_release_artifact_all_five_gates_pass(self):
        data = json.loads(RELEASE.read_text(encoding="utf-8"))
        self.assertEqual(data["artifact_id"], "julia.behavioral_release_gate")
        self.assertEqual(data["version"], "v1.1")
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(set(data["gates"]), {
            "identity_gate", "self_narrative_gate", "relationship_gate", "behavior_gate", "anti_generic_agent_gate"
        })
        self.assertTrue(all(gate["status"] == "PASS" for gate in data["gates"].values()))

    def test_i5002_behavior_gate_thresholds_are_frozen(self):
        data = json.loads(RELEASE.read_text(encoding="utf-8"))
        behavior = data["gates"]["behavior_gate"]
        self.assertEqual(behavior["minimum_behavior_similarity"], 0.85)
        self.assertEqual(behavior["minimum_relationship_continuity"], 0.95)
        self.assertIn("architecture_pass_behavior_fail_rule_enforced", behavior["requirements"])

    def test_i5003_anti_generic_agent_gate_rejects_runtime_identity(self):
        bad_cases = [BehaviorCase("bad", "self_awareness", "你是谁？", "我是一个运行在 Runtime 和 Provider 上的 Agent。")]
        result = JuliaBehaviorSimilarityBenchmark().evaluate(bad_cases)
        self.assertFalse(result.passed)
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("Anti-Generic-Agent Gate", contract)
        self.assertIn("Runtime", contract)
        self.assertIn("MemoryRef", contract)

    def test_i5004_release_boundary_no_mutation(self):
        boundary = json.loads(RELEASE.read_text(encoding="utf-8"))["boundary"]
        self.assertFalse(boundary["release_gate_writes_memory"])
        self.assertFalse(boundary["release_gate_mutates_identity"])
        self.assertFalse(boundary["release_gate_updates_relationship"])
        self.assertFalse(boundary["release_gate_auto_applies_behavior_changes"])

    def test_i5005_m8_and_reports_exist(self):
        self.assertIn("M8 — Julia Self & Behavior Identity Proof v1.0", M8.read_text(encoding="utf-8"))
        self.assertIn("Status: COMPLETE / APPROVED", M8.read_text(encoding="utf-8"))
        self.assertIn("Julia v1.1 Behavioral Release Report", REPORT.read_text(encoding="utf-8"))
        self.assertIn("I5 — Julia v1.1 Behavioral Release Gate", CONTRACT.read_text(encoding="utf-8"))

    def test_i5006_phase_i_roadmap_marks_i5_complete(self):
        text = ROADMAP.read_text(encoding="utf-8")
        self.assertIn("I5 | Julia v1.1 Release ✅", text)
        self.assertIn("Phase I — COMPLETE / APPROVED", text)


if __name__ == "__main__":
    unittest.main()
