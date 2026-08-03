import unittest
from pathlib import Path

from julia_core.client.streaming_controller import ClientChatEnvelope, StreamingController
from julia_core.runtime.assistant_runtime import JuliaAssistantRuntime, RuntimeStreamRequest

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server.py"
CONTROLLER = ROOT / "julia_core" / "client" / "streaming_controller.py"
RUNTIME = ROOT / "julia_core" / "runtime" / "assistant_runtime.py"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_H5_REAL_RUNTIME_BINDING.md"


class H5RealRuntimeBindingTest(unittest.TestCase):
    def test_h5001_runtime_stream_request_and_events(self):
        request = RuntimeStreamRequest(session_id="s-h5", message="Julia，我们继续讨论 Continuity OS。")
        events = tuple(JuliaAssistantRuntime().stream(request))
        self.assertEqual(events[0].event, "runtime_ready")
        self.assertIn("context_ready", [event.event for event in events])
        self.assertIn("text_delta", [event.event for event in events])
        self.assertEqual(events[-1].event, "done")

    def test_h5002_continuity_memory_context_provider_trace_present(self):
        result = StreamingController().complete_response(
            ClientChatEnvelope(text="为什么 Memory OS 不拥有 Identity？", session_id="s-h5", interaction_mode="text")
        )
        trace = result["trace"]
        self.assertEqual(trace["runtime"]["status"], "PASS")
        self.assertEqual(trace["continuity"]["status"], "PASS")
        self.assertEqual(trace["memory"]["status"], "PASS_BOUNDARY_NO_DUMP")
        self.assertEqual(trace["context"]["status"], "PASS")
        self.assertEqual(trace["provider"]["status"], "PASS")
        self.assertTrue(trace["provider"]["streaming"])

    def test_h5003_streaming_controller_emits_sse_from_runtime(self):
        chunks = tuple(
            StreamingController().stream_sse(
                ClientChatEnvelope(text="Julia streaming runtime", session_id="s-h5", interaction_mode="voice")
            )
        )
        joined = "".join(chunks)
        self.assertIn("event: runtime_ready", joined)
        self.assertIn("event: context_ready", joined)
        self.assertIn("event: text_delta", joined)
        self.assertIn("event: done", joined)

    def test_h5004_server_uses_controller_not_local_stream_stub(self):
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn("StreamingController", source)
        self.assertIn("STREAMING_CONTROLLER.stream_sse", source)
        self.assertNotIn("conversation_stream_events", source)
        self.assertNotIn("_streaming_trace", source)
        self.assertNotIn("_sse_stream", source)

    def test_h5005_streaming_layer_does_not_own_core_os(self):
        controller_source = CONTROLLER.read_text(encoding="utf-8")
        for forbidden in ("EvidenceScanner", "SemanticEvidenceRetriever", "RuntimeContinuityHook", "EvidenceContextReconstructor", "write_memory", "mutate_persona"):
            self.assertNotIn(forbidden, controller_source)

    def test_h5006_runtime_boundary_prevents_mutation_and_dumps(self):
        source = RUNTIME.read_text(encoding="utf-8")
        for forbidden in ("write_memory", "create_memory", "mutate_persona", "update_identity", "raw_memory_dumped\": True", "raw_evidence_dumped\": True"):
            self.assertNotIn(forbidden, source)

    def test_h5007_contract_documented(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("RuntimeStreamRequest", text)
        self.assertIn("RuntimeStreamEvent", text)
        self.assertIn("JuliaAssistantRuntime.stream", text)
        self.assertIn("StreamingController", text)


if __name__ == "__main__":
    unittest.main()
