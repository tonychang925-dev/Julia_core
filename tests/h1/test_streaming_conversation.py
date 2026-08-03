import json
import unittest
from pathlib import Path

from julia_core.client.streaming import StreamingTrace, chunk_text, conversation_stream_events

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server.py"
CONTROLLER = ROOT / "julia_core" / "client" / "streaming_controller.py"
APP_JS = ROOT / "julia_core" / "client" / "static" / "app.js"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_H4_STREAMING_CONVERSATION.md"


class H4StreamingConversationTest(unittest.TestCase):
    def test_h4001_stream_contract_objects_exist(self):
        trace = StreamingTrace(session_id="s1", interaction_mode="text")
        payload = trace.to_dict()
        self.assertTrue(payload["interaction"]["stream"])
        self.assertEqual(payload["runtime"]["session_id"], "s1")
        self.assertTrue(payload["provider"]["streaming"])
        self.assertFalse(payload["boundary"]["voice_owns_identity"])

    def test_h4002_response_chunks_are_ordered_and_final_marked(self):
        chunks = chunk_text("JuliaStreaming", chunk_size=5)
        self.assertEqual([chunk.index for chunk in chunks], [0, 1, 2])
        self.assertEqual("".join(chunk.text for chunk in chunks), "JuliaStreaming")
        self.assertTrue(chunks[-1].is_final)

    def test_h4003_stream_emits_trace_chunk_done(self):
        events = tuple(conversation_stream_events("hello Julia", StreamingTrace(session_id="s2", interaction_mode="voice"), chunk_size=5))
        self.assertEqual(events[0].event, "trace")
        self.assertIn("chunk", [event.event for event in events])
        self.assertEqual(events[-1].event, "done")

    def test_h4004_server_exposes_sse_endpoint(self):
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn('StreamingResponse', source)
        self.assertIn('@app.post("/api/chat/stream")', source)
        self.assertIn('text/event-stream', source)
        self.assertIn('STREAMING_CONTROLLER.stream_sse', source)
        self.assertIn('event: {event_name}', CONTROLLER.read_text(encoding='utf-8'))

    def test_h4005_frontend_uses_fetch_streaming_and_fallback(self):
        js = APP_JS.read_text(encoding="utf-8")
        self.assertIn("/api/chat/stream", js)
        self.assertIn("getReader", js)
        self.assertIn("parseSseEvent", js)
        self.assertIn("sendMessageFallback", js)

    def test_h4006_streaming_contract_documented(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("ConversationStreamEvent", text)
        self.assertIn("ResponseChunk", text)
        self.assertIn("StreamingTrace", text)

    def test_h4007_streaming_boundary_has_no_memory_identity_mutation_api(self):
        combined = SERVER.read_text(encoding="utf-8") + (ROOT / "julia_core" / "client" / "streaming.py").read_text(encoding="utf-8")
        forbidden = ["write_memory", "create_memory", "mutate_persona", "update_identity", "create_checkpoint", "provider_reads_files\": True"]
        for token in forbidden:
            self.assertNotIn(token, combined)


if __name__ == "__main__":
    unittest.main()
