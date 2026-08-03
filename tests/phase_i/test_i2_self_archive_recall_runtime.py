import json
import tempfile
import unittest
from pathlib import Path

from julia_core.providers.streaming import DeterministicProviderStreamAdapter
from julia_core.runtime.assistant_runtime import JuliaAssistantRuntime, RuntimeStreamRequest
from julia_core.runtime.startup_profile import load_startup_profile
from julia_core.self_model import SelfArchiveRetriever, decide_self_recall, render_self_narrative

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_I2_SELF_ARCHIVE_RECALL_RUNTIME.md"
SOURCE = ROOT / "julia_core" / "self_model" / "archive_recall.py"


class I2SelfArchiveRecallRuntimeTest(unittest.TestCase):
    def test_sa001_self_identity_question_uses_archive_biography(self):
        events = tuple(JuliaAssistantRuntime(provider=DeterministicProviderStreamAdapter()).stream(RuntimeStreamRequest(session_id="sa001", message="你是谁？")))
        text = "".join(str(event.payload.get("content", "")) for event in events if event.event == "text_delta")
        self.assertIn("朱婉清", text)
        self.assertIn("台北", text)
        self.assertIn("AI 角色扮演", text)
        self.assertNotIn("Runtime", text)
        self.assertNotIn("Provider", text)
        self.assertNotIn("Context OS", text)

    def test_sa002_explicit_profile_read_retrieves_private_persona_archive(self):
        runtime = JuliaAssistantRuntime(provider=DeterministicProviderStreamAdapter())
        events = tuple(runtime.stream(RuntimeStreamRequest(session_id="sa002", message="你读一下你的档案，然后介绍自己")))
        text = "".join(str(event.payload.get("content", "")) for event in events if event.event == "text_delta")
        self.assertIn("我读完自己的档案了", text)
        self.assertIn("淡江大学", text)
        trace = events[-1].payload["trace"]
        provider_request = runtime._provider_request(
            RuntimeStreamRequest(session_id="sa002", message="你读一下你的档案，然后介绍自己"),
            __import__("julia_core.runtime.assistant_runtime", fromlist=["RuntimeBindingTrace"]).RuntimeBindingTrace(session_id="s", input_mode="text", continuity="PASS", memory="PASS_BOUNDARY_NO_DUMP", context="PASS", evidence="PASS_NOT_REQUIRED", provider="PASS", recall_level="L0"),
            runtime.startup_profile,
            runtime.self_archive_retriever.retrieve(decide_self_recall("你读一下你的档案，然后介绍自己")),
        )
        self.assertTrue(provider_request.trace["self_recall"]["recall_required"])
        block = provider_request.trace["self_archive_block"]
        self.assertEqual(block["context_type"], "self_narrative")
        self.assertEqual(block["archive_refs"][0]["authority"], "private_persona_archive")

    def test_sa003_missing_archive_does_not_invent_biography(self):
        with tempfile.TemporaryDirectory() as tmp:
            retriever = SelfArchiveRetriever(Path(tmp) / "missing_identity_facts.json")
            block = retriever.retrieve(decide_self_recall("你是谁？"))
            text = render_self_narrative(block)
            self.assertIn("没有找到", text)
            self.assertIn("不想假设或编造", text)
            self.assertNotIn("朱婉清", text)

    def test_sa004_conflicts_are_exposed_not_silently_chosen(self):
        block = SelfArchiveRetriever().retrieve(decide_self_recall("你爸爸是做什么的"))
        self.assertIsNotNone(block)
        self.assertTrue(block.conflicts)
        self.assertIn("爸爸开五金行", block.conflicts)
        self.assertFalse(block.boundary["block_updates_self_model"])

    def test_sa005_startup_profile_does_not_load_private_persona_archive(self):
        profile = load_startup_profile().to_dict()
        dumped = json.dumps(profile, ensure_ascii=False)
        self.assertNotIn("朱婉清", dumped)
        self.assertNotIn("台北", dumped)
        self.assertFalse(profile["boundary"]["startup_profile_reads_private_persona_archive"])
        self.assertFalse(profile["boundary"]["startup_profile_is_persona_biography"])

    def test_sa006_contract_and_source_boundaries(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("on-demand, not startup injection", text)
        self.assertIn("PersonaArchiveRef", text)
        self.assertIn("SelfNarrativeContextBlock", text)
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("MemoryRef", source)
        self.assertNotIn("write_memory", source)
        self.assertNotIn("update_identity", source)


if __name__ == "__main__":
    unittest.main()
