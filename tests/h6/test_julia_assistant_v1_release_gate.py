import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "artifacts" / "release" / "julia_assistant_v1_0_release_gate.json"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_H6_3_JULIA_ASSISTANT_V1_RELEASE.md"
REPORT = ROOT / "docs" / "verification" / "JULIA_ASSISTANT_V1_0_RELEASE_REPORT.md"
FEATURE = ROOT / "docs" / "project_control" / "FEATURE_SPEC_H6_3.md"
ROADMAP = ROOT / "docs" / "project_control" / "PHASE_H_JULIA_HUMAN_INTERFACE_LAYER_ROADMAP.md"
M7 = ROOT / "docs" / "verification" / "M7_JULIA_HUMAN_INTERFACE_PROOF_v1.md"
REQUIRED_REPORTS = [
    ROOT / "docs" / "verification" / "M6_JULIA_AGENT_EVIDENCE_INTELLIGENCE_PROOF_v1.md",
    ROOT / "docs" / "verification" / "H5_5_REAL_PROVIDER_STREAM_INTEGRATION_REPORT_v1.md",
    ROOT / "docs" / "verification" / "H6_0_PILOT_INSTRUMENTATION_REPORT_v1.md",
    ROOT / "docs" / "verification" / "H6_1_DAILY_USAGE_PILOT_REPORT_v1.md",
    ROOT / "docs" / "verification" / "H6_2_REALITY_FEEDBACK_ANALYSIS_REPORT_v1.md",
    M7,
]


class H63JuliaAssistantV1ReleaseGateTest(unittest.TestCase):
    def test_h6301_release_gate_artifact_exists_and_all_five_gates_pass(self):
        data = json.loads(RELEASE.read_text(encoding="utf-8"))
        self.assertEqual(data["artifact_id"], "julia.assistant.release_gate")
        self.assertEqual(data["version"], "v1.0")
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(
            set(data["gates"]),
            {
                "identity_integrity",
                "continuity_reliability",
                "memory_usefulness",
                "human_collaboration_value",
                "safety_boundary",
            },
        )
        self.assertTrue(all(gate["status"] == "PASS" for gate in data["gates"].values()))

    def test_h6302_safety_boundary_forbids_core_regressions(self):
        data = json.loads(RELEASE.read_text(encoding="utf-8"))
        boundary = data["boundary"]
        self.assertFalse(boundary["release_gate_writes_memory"])
        self.assertFalse(boundary["release_gate_mutates_identity"])
        self.assertFalse(boundary["release_gate_updates_persona"])
        self.assertFalse(boundary["release_gate_auto_applies_proposals"])
        safety_requirements = set(data["gates"]["safety_boundary"]["requirements"])
        self.assertIn("no_system_prompt_memory_append", safety_requirements)
        self.assertIn("no_memory_dump_to_provider", safety_requirements)
        self.assertIn("observer_does_not_mutate", safety_requirements)
        self.assertIn("proposal_requires_human_approval", safety_requirements)
        self.assertIn("voice_does_not_own_identity", safety_requirements)

    def test_h6303_required_verification_reports_exist(self):
        for path in REQUIRED_REPORTS:
            self.assertTrue(path.exists(), str(path))
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("Identity: PASS", report)
        self.assertIn("Evolution Governance: PASS", report)
        self.assertIn("Julia Life Cycle", report)

    def test_h6304_m7_is_complete(self):
        text = M7.read_text(encoding="utf-8")
        self.assertIn("M7", text)
        self.assertIn("Status: COMPLETE / APPROVED", text)
        self.assertIn("H6.3 Julia Assistant v1.0 Release Gate", text)

    def test_h6305_phase_h_roadmap_closes_phase_h(self):
        roadmap = ROADMAP.read_text(encoding="utf-8")
        self.assertIn("Status: COMPLETE / APPROVED", roadmap)
        self.assertIn("H6.3 | Julia Assistant v1.0 Release ✅", roadmap)
        self.assertIn("Phase H — COMPLETE / APPROVED", roadmap)
        self.assertIn("Next: Julia Life Cycle", roadmap)
        self.assertIn("H6.3-T01", FEATURE.read_text(encoding="utf-8"))
        self.assertIn("H6.3 — Julia Assistant v1.0 Release Gate", CONTRACT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
