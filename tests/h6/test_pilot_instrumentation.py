import tempfile
import unittest
from pathlib import Path

from julia_core.client.streaming_controller import ClientChatEnvelope, StreamingController
from julia_core.observer import JsonlPilotObserver, record_from_runtime_trace, summarize_observations

ROOT = Path(__file__).resolve().parents[2]
OBSERVER = ROOT / "julia_core" / "observer" / "pilot_observer.py"
CONTROLLER = ROOT / "julia_core" / "client" / "streaming_controller.py"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_H6_0_PILOT_INSTRUMENTATION.md"
REPORT = ROOT / "docs" / "verification" / "H6_0_PILOT_INSTRUMENTATION_REPORT_v1.md"
ROADMAP = ROOT / "docs" / "project_control" / "PHASE_H_JULIA_HUMAN_INTERFACE_LAYER_ROADMAP.md"


class H60PilotInstrumentationTest(unittest.TestCase):
    def test_h6001_record_from_runtime_trace_maps_core_metrics_without_mutation(self):
        trace = {
            "continuity": {"status": "PASS"},
            "memory": {"status": "PASS_BOUNDARY_NO_DUMP"},
            "context": {"status": "PASS", "blocks_used": ["identity_boundary"]},
            "evidence": {"status": "PASS", "refs": ["evidence://ADR-017"]},
        }
        record = record_from_runtime_trace(
            session_id="pilot-session",
            duration_ms=1200,
            trace=trace,
            input_mode="voice",
            voice_output=True,
        )
        self.assertEqual(record.session, "pilot-session")
        self.assertTrue(record.continuity.checkpoint_used)
        self.assertTrue(record.continuity.reconstruction_required)
        self.assertTrue(record.evidence.retrieval_triggered)
        self.assertTrue(record.evidence.successful)
        self.assertTrue(record.voice.input)
        self.assertTrue(record.voice.output)
        self.assertFalse(record.boundary["observer_writes_memory"])
        self.assertFalse(record.boundary["observer_mutates_identity"])

    def test_h6002_jsonl_observer_appends_and_summarizes_pilot_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pilot.jsonl"
            observer = JsonlPilotObserver(path)
            trace = {
                "continuity": {"status": "PASS"},
                "memory": {"status": "PASS"},
                "context": {"status": "PASS", "blocks_used": []},
                "evidence": {"status": "PASS_NOT_REQUIRED", "refs": []},
            }
            observer.observe(record_from_runtime_trace(session_id="s1", duration_ms=10, trace=trace, input_mode="text"))
            observer.observe(record_from_runtime_trace(session_id="s1", duration_ms=12, trace=trace, input_mode="voice", voice_output=True))
            records = observer.read_records()
            summary = summarize_observations(records)
            self.assertEqual(len(records), 2)
            self.assertEqual(summary.total_sessions, 1)
            self.assertEqual(summary.total_turns, 2)
            self.assertEqual(summary.voice_usage_ratio, 0.5)
            self.assertEqual(summary.human_friction_score, 0)

    def test_h6003_streaming_controller_records_completed_turns(self):
        with tempfile.TemporaryDirectory() as tmp:
            observer = JsonlPilotObserver(Path(tmp) / "pilot.jsonl")
            controller = StreamingController(observer=observer)
            result = controller.complete_response(
                ClientChatEnvelope(text="Julia，继续 H6 Pilot。", session_id="pilot-stream", interaction_mode="voice", voice_output=True)
            )
            self.assertIn("trace", result)
            records = observer.read_records()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].session, "pilot-stream")
            self.assertTrue(records[0].voice.input)
            self.assertTrue(records[0].voice.output)

    def test_h6004_observer_isolation_from_core_authority(self):
        source = OBSERVER.read_text(encoding="utf-8")
        forbidden = [
            "julia_core.memory",
            "julia_core.continuity",
            "julia_core.evidence",
            "julia_core.context_os",
            "write_memory",
            "create_memory",
            "mutate_persona",
            "update_identity",
            "ProviderStreamAdapter",
        ]
        for token in forbidden:
            self.assertNotIn(token, source)
        controller_source = CONTROLLER.read_text(encoding="utf-8")
        self.assertIn("record_from_runtime_trace", controller_source)
        self.assertNotIn("observer_writes_memory\": True", controller_source)

    def test_h6005_contract_report_and_roadmap_document_h6(self):
        self.assertIn("H6.0 — Pilot Instrumentation", CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("Observation Layer", CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("H6.0 Pilot Instrumentation", REPORT.read_text(encoding="utf-8"))
        roadmap = ROADMAP.read_text(encoding="utf-8")
        self.assertIn("H6.0 | Pilot Instrumentation", roadmap)
        self.assertIn("H6.1 | Tony-Julia Daily Usage Pilot", roadmap)


if __name__ == "__main__":
    unittest.main()
