import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "artifacts" / "operation" / "julia_governance_loop_v1.json"
GOV_DOC = ROOT / "docs" / "operation" / "JULIA_GOVERNANCE_LOOP_v1.md"
PILOT = ROOT / "docs" / "operation" / "OPERATION_CYCLE_1_30_DAY_PILOT.md"
FREEZE = ROOT / "docs" / "project_control" / "JULIA_SECOND_ARCHITECTURE_FREEZE_OPERATING_MODE.md"
FEATURE = ROOT / "docs" / "project_control" / "FEATURE_SPEC_GOVERNANCE_LOOP_V1.md"
OPERATING = ROOT / "artifacts" / "operation" / "julia_operating_mode_v1.json"


class GovernanceLoopV1Test(unittest.TestCase):
    def test_gl001_governance_loop_artifact_records_second_freeze(self):
        data = json.loads(GOV.read_text(encoding="utf-8"))
        self.assertEqual(data["artifact_id"], "julia.governance_loop")
        self.assertEqual(data["status"], "FROZEN")
        self.assertEqual(data["freeze_order"], 2)
        self.assertEqual(data["previous_freeze_point"], "Julia Core v1.0 Architecture Freeze")
        self.assertEqual(data["architecture_freeze_point"], "Julia Assistant v1.0 Operating Mode Activated")
        self.assertEqual(data["governance_loop"][0], "Real Daily Use")
        self.assertEqual(data["governance_loop"][-1], "Regression Verification")

    def test_gl002_growth_philosophy_and_boundaries_are_frozen(self):
        data = json.loads(GOV.read_text(encoding="utf-8"))
        self.assertFalse(data["growth_philosophy"]["experience_is_identity"])
        self.assertFalse(data["growth_philosophy"]["observation_is_memory"])
        self.assertFalse(data["growth_philosophy"]["proposal_is_evolution"])
        self.assertFalse(data["growth_philosophy"]["evolution_is_drift"])
        self.assertFalse(data["boundary"]["governance_loop_adds_core_os"])
        self.assertFalse(data["boundary"]["governance_loop_auto_applies_proposals"])
        doc = GOV_DOC.read_text(encoding="utf-8")
        self.assertIn("Experience ≠ Identity", doc)
        self.assertIn("Observation ≠ Memory", doc)
        self.assertIn("Proposal ≠ Evolution", doc)
        self.assertIn("Evolution ≠ Drift", doc)

    def test_gl003_operation_cycle_1_is_priority_zero_before_dashboard(self):
        data = json.loads(GOV.read_text(encoding="utf-8"))
        self.assertEqual(data["priority_order"][0], "Operation Cycle 1 — 30 Day Pilot")
        self.assertEqual(data["priority_order"][1], "Julia Health Dashboard")
        pilot = PILOT.read_text(encoding="utf-8")
        self.assertIn("Priority 0", pilot)
        self.assertIn("Does Tony naturally want to use Julia every day?", pilot)
        self.assertIn("No Dashboard-first optimization", pilot)

    def test_gl004_dashboard_and_review_ui_are_governance_surfaces_not_control(self):
        data = json.loads(GOV.read_text(encoding="utf-8"))
        self.assertTrue(data["dashboard_boundary"]["is_observation_window"])
        self.assertFalse(data["dashboard_boundary"]["is_control_panel"])
        self.assertTrue(data["review_ui_boundary"]["approve_reject_required"])
        self.assertFalse(data["review_ui_boundary"]["auto_apply_allowed"])
        self.assertFalse(data["boundary"]["dashboard_controls_identity"])

    def test_gl005_second_freeze_docs_and_operating_mode_are_consistent(self):
        self.assertTrue(OPERATING.exists())
        freeze = FREEZE.read_text(encoding="utf-8")
        self.assertIn("Second Architecture Freeze", freeze)
        self.assertIn("Julia Core v1.0 Architecture Freeze", freeze)
        self.assertIn("Julia Assistant v1.0 Operating Mode Activated", freeze)
        self.assertIn("GL-v1-T01", FEATURE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
