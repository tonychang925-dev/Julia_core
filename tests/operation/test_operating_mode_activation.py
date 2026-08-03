import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "artifacts" / "operation" / "julia_operating_mode_v1.json"
CYCLE = ROOT / "docs" / "operation" / "JULIA_OPERATION_CYCLE_v1.md"
CONTRACT = ROOT / "docs" / "project_control" / "JULIA_ASSISTANT_V1_OPERATING_MODE_CONTRACT.md"
REPORT = ROOT / "docs" / "verification" / "JULIA_OPERATING_MODE_ACTIVATION_REPORT.md"
FEATURE = ROOT / "docs" / "project_control" / "FEATURE_SPEC_OPERATING_MODE_V1.md"
RELEASE = ROOT / "artifacts" / "release" / "julia_assistant_v1_0_release_gate.json"
M7 = ROOT / "docs" / "verification" / "M7_JULIA_HUMAN_INTERFACE_PROOF_v1.md"


class OperatingModeActivationTest(unittest.TestCase):
    def test_om001_operating_mode_artifact_activates_v1(self):
        data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(data["artifact_id"], "julia.operating_mode")
        self.assertEqual(data["status"], "ACTIVE")
        self.assertEqual(data["title"], "Julia Assistant v1.0 — Operating Mode Activated")
        self.assertEqual(data["mode_transition"]["from"], "building_mode")
        self.assertEqual(data["mode_transition"]["to"], "operating_mode")
        self.assertEqual(data["operation_cycle"], ["Observe", "Understand", "Propose", "Approve", "Evolve", "Verify"])

    def test_om002_life_cycle_tracks_are_documented(self):
        data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(set(data["life_cycle_tracks"]), {
            "L1_continuous_operation",
            "L2_relationship_evolution",
            "L3_governed_evolution",
            "L4_release_cycle",
        })
        text = CYCLE.read_text(encoding="utf-8")
        self.assertIn("L1 — Continuous Operation", text)
        self.assertIn("L2 — Relationship Evolution", text)
        self.assertIn("L3 — Governed Evolution", text)
        self.assertIn("L4 — Julia Release Cycle", text)
        self.assertIn("Collaboration Continuity Score", text)

    def test_om003_core_freeze_boundary_prevents_phase_i_expansion(self):
        data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(data["core_freeze"]["status"], "FROZEN")
        self.assertFalse(data["boundary"]["operating_mode_adds_core_os"])
        self.assertFalse(data["boundary"]["operating_mode_writes_memory"])
        self.assertFalse(data["boundary"]["operating_mode_mutates_identity"])
        self.assertFalse(data["boundary"]["operating_mode_auto_applies_proposals"])
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("Does this improve Julia operation?", contract)
        self.assertIn("not merely", contract)

    def test_om004_milestone_chain_and_release_gate_complete(self):
        self.assertTrue(RELEASE.exists())
        self.assertIn("Status: COMPLETE / APPROVED", M7.read_text(encoding="utf-8"))
        contract = CONTRACT.read_text(encoding="utf-8")
        for milestone in ("M1", "M2", "M3", "M4", "M5", "M6", "M7"):
            self.assertIn(milestone, contract)
        self.assertIn("Julia Assistant v1.0", contract)
        self.assertIn("Operating Mode Activated", REPORT.read_text(encoding="utf-8"))
        self.assertIn("OM-v1-T01", FEATURE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
