import json
import unittest
from pathlib import Path

ARTIFACT = Path("artifacts/continuity/julia_continuity_state_v1.json")


class TestK70ContinuityStateContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_continuity_state_artifact_exists_and_is_versioned(self):
        self.assertTrue(ARTIFACT.exists())
        self.assertEqual(self.data["artifact_id"], "julia.continuity_state")
        self.assertEqual(self.data["version"], "v1")

    def test_required_layers_include_experience_and_calibration(self):
        layers = self.data["required_layers"]
        self.assertTrue(layers["identity_required"])
        self.assertTrue(layers["self_model_required"])
        self.assertTrue(layers["relationship_required"])
        self.assertTrue(layers["experience_required"])
        self.assertTrue(layers["experience_calibration_required"])
        self.assertTrue(layers["context_reconstruction_required"])

    def test_reconstruction_order_is_explicit(self):
        self.assertEqual(
            self.data["reconstruction_order"],
            ["identity", "self_model", "relationship", "experience", "experience_calibration", "context"],
        )

    def test_forbidden_shortcuts_are_declared(self):
        forbidden = set(self.data["forbidden_shortcuts"])
        self.assertIn("raw_memory_dump", forbidden)
        self.assertIn("persona_prompt", forbidden)
        self.assertIn("fixed_roleplay", forbidden)
        self.assertIn("provider_direct_state_access", forbidden)
        self.assertIn("experience_without_history", forbidden)
        self.assertIn("identity_mutation_from_experience", forbidden)

    def test_k7_five_gates_declared(self):
        gates = self.data["recovery_gates"]
        self.assertTrue(gates["identity_recovery"])
        self.assertTrue(gates["relationship_recovery"])
        self.assertTrue(gates["experience_recovery"])
        self.assertTrue(gates["continuity_naturalness"])
        self.assertTrue(gates["provider_transfer"])

    def test_boundary(self):
        boundary = self.data["boundary"]
        self.assertFalse(boundary["continuity_state_is_memory"])
        self.assertFalse(boundary["continuity_state_is_persona"])
        self.assertFalse(boundary["continuity_state_mutates_identity"])
        self.assertFalse(boundary["continuity_state_stores_raw_conversation"])
        self.assertFalse(boundary["continuity_state_allows_fixed_roleplay"])


if __name__ == "__main__":
    unittest.main()
