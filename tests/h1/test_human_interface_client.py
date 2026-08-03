import py_compile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server.py"
CONTROLLER = ROOT / "julia_core" / "client" / "streaming_controller.py"
RUNTIME = ROOT / "julia_core" / "runtime" / "assistant_runtime.py"
INDEX = ROOT / "julia_core" / "client" / "static" / "index.html"
APP_JS = ROOT / "julia_core" / "client" / "static" / "app.js"
CSS = ROOT / "julia_core" / "client" / "static" / "styles.css"


class H1HumanInterfaceClientTest(unittest.TestCase):
    def test_h1001_server_compiles_and_mounts_client(self):
        py_compile.compile(str(SERVER), doraise=True)
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn('app.mount("/client"', source)
        self.assertIn('@app.get("/")', source)
        self.assertIn('@app.post("/api/chat")', source)
        self.assertIn("StreamingController", source)

    def test_h1002_index_serves_chat_client_structure(self):
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("Julia Client", html)
        self.assertIn("messages", html)
        self.assertIn("trace", html)
        self.assertIn("voice-in", html)
        self.assertIn("voice-out", html)

    def test_h1003_text_chat_api_trace_contract_exists(self):
        runtime_source = RUNTIME.read_text(encoding="utf-8")
        controller_source = CONTROLLER.read_text(encoding="utf-8")
        self.assertIn('"interaction"', runtime_source)
        self.assertIn('"runtime"', runtime_source)
        self.assertIn('"boundary"', runtime_source)
        self.assertIn("complete_response", controller_source)
        self.assertIn('"streaming_layer_mutates_identity": False', runtime_source)
        self.assertIn('"streaming_layer_writes_memory": False', runtime_source)

    def test_h2001_voice_input_trace_uses_browser_stt_adapter(self):
        js = APP_JS.read_text(encoding="utf-8")
        runtime_source = RUNTIME.read_text(encoding="utf-8")
        self.assertIn("SpeechRecognition", js)
        self.assertIn("speechSynthesis", js)
        self.assertIn('"voice_owns_identity": False', runtime_source)

    def test_h3001_client_contains_browser_voice_adapters(self):
        js = APP_JS.read_text(encoding="utf-8")
        self.assertIn("SpeechRecognition", js)
        self.assertIn("speechSynthesis", js)
        self.assertIn("interaction_mode", js)
        self.assertIn("sendMessage(text, 'voice')", js)
        self.assertTrue(CSS.exists())


if __name__ == "__main__":
    unittest.main()
