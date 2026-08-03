import unittest
from pathlib import Path

from julia_core.voice import VoiceProfile, VoiceService, default_julia_voice_profile
from julia_core.voice.tts_adapter import TTSRequest, TTSResult

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server.py"
APP_JS = ROOT / "julia_core" / "client" / "static" / "app.js"
VOICE_DIR = ROOT / "julia_core" / "voice"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_H3_5_VOICE_IDENTITY_BINDING.md"


class FakeTTSProvider:
    provider_id = "fake_edge_tts"

    def synthesize(self, request: TTSRequest) -> TTSResult:
        return TTSResult(ok=True, audio=b"ID3FAKEAUDIO", media_type="audio/mpeg", provider=request.profile.provider, voice=request.profile.voice)


class H35VoiceIdentityBindingTest(unittest.TestCase):
    def test_h3501_default_voice_profile_matches_julia_edge_tts(self):
        profile = default_julia_voice_profile()
        self.assertEqual(profile.voice_id, "julia.voice.v1")
        self.assertEqual(profile.provider, "edge_tts")
        self.assertEqual(profile.engine, "neural")
        self.assertEqual(profile.voice, "zh-CN-XiaoxiaoNeural")
        self.assertEqual(profile.audio_format, "audio/mpeg")

    def test_h3502_voice_service_returns_audio_without_identity_authority(self):
        service = VoiceService(provider=FakeTTSProvider(), profile=VoiceProfile("julia.voice.v1", "edge_tts", "neural", "zh-CN-XiaoxiaoNeural"))
        result = service.synthesize("Tony，我在。")
        self.assertTrue(result.ok)
        self.assertEqual(result.audio, b"ID3FAKEAUDIO")
        trace = result.trace()
        self.assertFalse(trace["boundary"]["voice_owns_identity"])
        self.assertFalse(trace["boundary"]["voice_writes_memory"])
        self.assertFalse(trace["boundary"]["voice_mutates_persona"])

    def test_h3503_server_exposes_voice_service_api(self):
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn("VoiceService", source)
        self.assertIn('@app.get("/api/voice/profile")', source)
        self.assertIn('@app.post("/api/voice/synthesize")', source)
        self.assertIn('media_type=result.media_type', source)

    def test_h3504_client_uses_voice_service_before_browser_fallback(self):
        js = APP_JS.read_text(encoding="utf-8")
        self.assertIn("/api/voice/synthesize", js)
        self.assertIn("new Audio", js)
        self.assertIn("edge_tts_failed", js)
        self.assertIn("speechSynthesis", js)  # fallback only
        self.assertLess(js.index("/api/voice/synthesize"), js.index("speechSynthesis"))

    def test_h3505_voice_layer_has_no_core_authority_imports(self):
        combined = "\n".join(path.read_text(encoding="utf-8") for path in VOICE_DIR.glob("*.py"))
        forbidden = ["julia_core.memory", "julia_core.continuity", "julia_core.evidence", "mutate_persona", "update_identity", "write_memory"]
        for token in forbidden:
            self.assertNotIn(token, combined)

    def test_h3506_contract_documented(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("H3.5 Julia Voice Identity Binding", text)
        self.assertIn("zh-CN-XiaoxiaoNeural", text)
        self.assertIn("Voice is expression, not identity authority", text)


if __name__ == "__main__":
    unittest.main()
