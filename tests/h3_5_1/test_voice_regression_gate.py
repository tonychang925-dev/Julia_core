import json
import unittest
from pathlib import Path

from julia_core.voice import VoiceService, default_julia_voice_profile, load_voice_artifact
from julia_core.voice.tts_adapter import TTSRequest, TTSResult

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "artifacts" / "voice" / "julia_voice_v1.json"
VOICE_DIR = ROOT / "julia_core" / "voice"
APP_JS = ROOT / "julia_core" / "client" / "static" / "app.js"
SERVER = ROOT / "server.py"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_H3_5_1_VOICE_REGRESSION_GATE.md"


class FailingTTSProvider:
    provider_id = "failing_edge_tts"

    def synthesize(self, request: TTSRequest) -> TTSResult:
        return TTSResult(ok=False, audio=b"", media_type="audio/mpeg", provider=request.profile.provider, voice=request.profile.voice, error="edge_unavailable")


class VoiceRegressionGateTest(unittest.TestCase):
    def test_v001_voice_profile_stability(self):
        artifact = load_voice_artifact(ARTIFACT)
        self.assertEqual(artifact["artifact_id"], "julia.voice")
        self.assertEqual(artifact["version"], "v1")
        self.assertEqual(artifact["provider"], "edge_tts")
        self.assertEqual(artifact["voice"], "zh-CN-XiaoxiaoNeural")
        profile = default_julia_voice_profile()
        self.assertEqual(profile.voice_id, "julia.voice.v1")
        self.assertEqual(profile.voice, "zh-CN-XiaoxiaoNeural")

    def test_v002_provider_failure_fallback_contract(self):
        service = VoiceService(provider=FailingTTSProvider(), profile=default_julia_voice_profile())
        result = service.synthesize("Tony，我在。")
        self.assertFalse(result.ok)
        trace = service.fallback_trace(result.error)
        self.assertEqual(trace["voice"]["provider"], "browser_fallback")
        self.assertEqual(trace["voice"]["status"], "DEGRADED")
        self.assertFalse(trace["boundary"]["voice_owns_identity"])
        self.assertFalse(trace["boundary"]["voice_writes_memory"])
        self.assertIn("HTTPException(status_code=503", SERVER.read_text(encoding="utf-8"))
        self.assertIn("edge_tts_failed", APP_JS.read_text(encoding="utf-8"))

    def test_v003_voice_isolation(self):
        combined = "\n".join(path.read_text(encoding="utf-8") for path in VOICE_DIR.glob("*.py"))
        forbidden = ["julia_core.memory", "julia_core.continuity", "julia_core.evidence", "julia_core.persona", "identity", "write_memory", "mutate_persona"]
        # The public boundary field may contain identity wording; authority imports/mutation APIs must not exist.
        forbidden.remove("identity")
        for token in forbidden:
            self.assertNotIn(token, combined)
        artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertFalse(artifact["boundary"]["voice_owns_identity"])
        self.assertFalse(artifact["boundary"]["voice_writes_memory"])

    def test_v004_contract_documented(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("V-001", text)
        self.assertIn("V-002", text)
        self.assertIn("V-003", text)
        self.assertIn("artifacts/voice/julia_voice_v1.json", text)


if __name__ == "__main__":
    unittest.main()
