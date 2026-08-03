import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "docs" / "project_control" / "PHASE_H_JULIA_HUMAN_INTERFACE_LAYER_ROADMAP.md"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_H0_CLIENT_ARCHITECTURE_FREEZE.md"
CLIENT_APP = ROOT / "julia_core" / "client" / "static" / "app.js"


class H0ClientArchitectureContractTest(unittest.TestCase):
    def test_h0001_phase_h_docs_exist(self):
        self.assertTrue(ROADMAP.exists())
        self.assertTrue(CONTRACT.exists())
        self.assertIn("Julia Human Interface Layer", ROADMAP.read_text(encoding="utf-8"))
        self.assertIn("H0 Client Architecture Freeze", CONTRACT.read_text(encoding="utf-8"))

    def test_h0002_voice_is_interaction_not_identity(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("Voice → Identity authority", text)
        self.assertIn("Voice transcript → automatic Memory write", text)
        app = CLIENT_APP.read_text(encoding="utf-8")
        for forbidden in ("updateIdentity", "writeMemory", "personaArtifact", "createCheckpoint"):
            self.assertNotIn(forbidden, app)


if __name__ == "__main__":
    unittest.main()
