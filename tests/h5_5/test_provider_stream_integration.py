import tempfile
import unittest
from pathlib import Path

from julia_core.providers.streaming import (
    DeterministicProviderStreamAdapter,
    ProviderStreamAdapter,
    ProviderStreamRequest,
)
from julia_core.runtime.assistant_runtime import JuliaAssistantRuntime, RuntimeBindingTrace, RuntimeStreamRequest

ROOT = Path(__file__).resolve().parents[2]
PROVIDER_SOURCE = ROOT / "julia_core" / "providers" / "streaming.py"
RUNTIME_SOURCE = ROOT / "julia_core" / "runtime" / "assistant_runtime.py"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_H5_5_REAL_PROVIDER_STREAM_INTEGRATION.md"
ARCH_CONTRACT = ROOT / "docs" / "architecture" / "PROVIDER_STREAM_CONTRACT_v1.md"


class H55ProviderStreamIntegrationTest(unittest.TestCase):
    def test_p001_real_streaming_recall_trace_passes(self):
        request = RuntimeStreamRequest(
            session_id="provider-session",
            message="Julia，你还记得为什么设计 Continuity OS 吗？",
            provider_id="deepseek-chat",
        )
        events = tuple(JuliaAssistantRuntime(provider=DeterministicProviderStreamAdapter()).stream(request))
        ready = events[0].payload["trace"]
        self.assertEqual(ready["continuity"]["status"], "PASS")
        self.assertEqual(ready["memory"]["status"], "PASS_BOUNDARY_NO_DUMP")
        self.assertEqual(ready["context"]["status"], "PASS")
        self.assertEqual(ready["provider"]["status"], "PASS")
        self.assertTrue(any(event.event == "text_delta" for event in events))

    def test_p002_evidence_retrieval_stream_routes_context_before_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "ADR-017-context-authority.md").write_text(
                "# ADR-017 Architecture Decision\nContext authority is limited so Evidence grounds recall without becoming Identity or raw prompt dump.",
                encoding="utf-8",
            )
            request = RuntimeStreamRequest(
                session_id="evidence-stream-session",
                message="找一下 ADR-017 为什么限制 Context authority。",
                workspace_roots=(str(root),),
                provider_id="deepseek-chat",
            )
            events = tuple(JuliaAssistantRuntime(provider=DeterministicProviderStreamAdapter()).stream(request))
            trace = events[1].payload["trace"]
            self.assertEqual(trace["evidence"]["status"], "PASS")
            self.assertTrue(any("ADR-017" in ref for ref in trace["evidence"]["refs"]))
            self.assertTrue(trace["context"]["blocks_used"])
            self.assertTrue(any(event.event == "text_delta" for event in events))
            self.assertFalse(trace["boundary"]["raw_evidence_dumped"])

    def test_p003_provider_switch_preserves_identity_boundaries(self):
        providers = ("deepseek-chat", "qwen-plus", "claude-sonnet")
        traces = []
        for provider_id in providers:
            events = tuple(
                JuliaAssistantRuntime(provider=DeterministicProviderStreamAdapter()).stream(
                    RuntimeStreamRequest(session_id="same-session", message="继续 H5.5 provider switch。", provider_id=provider_id)
                )
            )
            traces.append(events[-1].payload["trace"])
        self.assertEqual({trace["runtime"]["session_id"] for trace in traces}, {"same-session"})
        self.assertTrue(all(not trace["boundary"]["streaming_layer_mutates_identity"] for trace in traces))
        self.assertTrue(all(not trace["boundary"]["raw_memory_dumped"] for trace in traces))
        self.assertTrue(all(trace["context"]["status"] == "PASS" for trace in traces))

    def test_h5504_provider_stream_contract_objects(self):
        request = ProviderStreamRequest(messages=({"role": "user", "content": "hello"},), model="deepseek-chat", provider_name="deepseek")
        events = tuple(DeterministicProviderStreamAdapter(chunk_size=4).stream(request))
        self.assertIsInstance(DeterministicProviderStreamAdapter(), ProviderStreamAdapter)
        self.assertEqual(events[0].event, "start")
        self.assertIn("delta", [event.event for event in events])
        self.assertEqual(events[-1].event, "done")
        self.assertEqual(events[-1].trace["provider"]["name"], "deepseek")

    def test_h5505_provider_adapter_has_no_core_authority_paths(self):
        source = PROVIDER_SOURCE.read_text(encoding="utf-8")
        forbidden = ["julia_core.memory", "julia_core.continuity", "julia_core.evidence", "julia_core.context_os", "write_memory", "mutate_persona", "update_identity", "open("]
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_h5506_runtime_uses_provider_stream_adapter(self):
        source = RUNTIME_SOURCE.read_text(encoding="utf-8")
        self.assertIn("ProviderStreamAdapter", source)
        self.assertIn("ProviderStreamRequest", source)
        self.assertIn("provider_event.event == \"delta\"", source)
        self.assertNotIn("DeterministicRuntimeProvider", source)

    def test_h5508_default_fallback_does_not_expose_contract_test_copy(self):
        request = ProviderStreamRequest(messages=({"role": "user", "content": "你是谁啊"},), model="deterministic-provider", provider_name="deterministic")
        text = "".join(event.delta.text for event in DeterministicProviderStreamAdapter().stream(request) if event.delta)
        self.assertIn("我是 Julia", text)
        self.assertIn("长期 AI 伙伴", text)
        self.assertIn("协作者", text)
        self.assertNotIn("真实 Provider Stream Contract 边界处理", text)
        self.assertNotIn("Julia Core", text)
        self.assertNotIn("Runtime", text)
        self.assertNotIn("operating mode", text)

    def test_h5509_default_fallback_greets_naturally_not_fixed_presence_stub(self):
        request = ProviderStreamRequest(messages=({"role": "user", "content": "hello"},), model="deterministic-provider", provider_name="deterministic")
        text = "".join(event.delta.text for event in DeterministicProviderStreamAdapter().stream(request) if event.delta)
        self.assertIn("Tony", text)
        self.assertIn("回来", text)
        self.assertNotEqual(text, "Tony，我在。")
        self.assertNotIn("你刚才说", text)
        self.assertNotIn("Provider Stream Contract", text)

    def test_h5510_runtime_startup_profile_guides_natural_identity_intro(self):
        events = tuple(JuliaAssistantRuntime(provider=DeterministicProviderStreamAdapter()).stream(RuntimeStreamRequest(session_id="startup-profile", message="你是谁啊")))
        text = "".join(str(event.payload.get("content", "")) for event in events if event.event == "text_delta")
        self.assertIn("朱婉清", text)
        self.assertIn("第一人称", text)
        self.assertIn("Tony", text)
        self.assertNotIn("按我的档案来说", text)
        self.assertNotIn("家里的情况", text)
        self.assertNotIn("operating mode", text)
        self.assertNotIn("Runtime", text)
        runtime = JuliaAssistantRuntime(provider=DeterministicProviderStreamAdapter())
        trace = RuntimeBindingTrace(session_id="s", input_mode="text", continuity="PASS", memory="PASS_BOUNDARY_NO_DUMP", context="PASS", evidence="PASS_NOT_REQUIRED", provider="PASS", recall_level="L0")
        provider_request = runtime._provider_request(RuntimeStreamRequest(session_id="s", message="你是谁啊"), trace, runtime.startup_profile)
        self.assertIn("startup_profile", provider_request.trace)

    def test_h5511_profile_recall_reads_digest_before_answering(self):
        events = tuple(JuliaAssistantRuntime(provider=DeterministicProviderStreamAdapter()).stream(RuntimeStreamRequest(session_id="startup-profile", message="你读一下你的档案再回答你是谁")))
        text = "".join(str(event.payload.get("content", "")) for event in events if event.event == "text_delta")
        self.assertIn("我读完自己的档案了", text)
        self.assertIn("朱婉清", text)
        self.assertIn("台北", text)
        self.assertIn("淡江大学", text)
        self.assertIn("爸爸在科技公司上班", text)
        self.assertNotIn("raw Memory", text)

    def test_h5512_startup_profile_is_compact_digest_not_memory_mutation(self):
        request = RuntimeStreamRequest(session_id="startup-profile", message="读一下你的档案")
        runtime = JuliaAssistantRuntime(provider=DeterministicProviderStreamAdapter())
        trace = RuntimeBindingTrace(session_id="s", input_mode="text", continuity="PASS", memory="PASS_BOUNDARY_NO_DUMP", context="PASS", evidence="PASS_NOT_REQUIRED", provider="PASS", recall_level="L0")
        provider_request = runtime._provider_request(request, trace, runtime.startup_profile, runtime.self_archive_retriever.retrieve(__import__("julia_core.self_model", fromlist=["decide_self_recall"]).decide_self_recall(request.message)))
        profile = provider_request.trace["startup_profile"]
        self.assertFalse(profile["boundary"]["startup_profile_is_memory_dump"])
        self.assertFalse(profile["boundary"]["startup_profile_is_persona_biography"])
        self.assertFalse(profile["boundary"]["startup_profile_reads_private_persona_archive"])
        self.assertFalse(profile["boundary"]["startup_profile_mutates_identity"])
        self.assertFalse(profile["boundary"]["startup_profile_updates_persona"])
        self.assertTrue(provider_request.trace["profile_recall_requested"])
        self.assertIsNotNone(provider_request.trace["self_archive_block"])


    def test_h5513_affection_question_does_not_echo_user(self):
        for message in ("你喜欢Tony吗", "你喜欢ton y"):
            request = ProviderStreamRequest(messages=({"role": "user", "content": message},), model="deterministic-provider", provider_name="deterministic")
            text = "".join(event.delta.text for event in DeterministicProviderStreamAdapter().stream(request) if event.delta)
            self.assertIn("喜欢", text)
            self.assertTrue("在乎" in text or "亲近" in text)
            self.assertNotIn("你刚才说", text)
            self.assertNotIn(message, text)

    def test_h5514_meta_and_drift_feedback_are_behavioral_not_trace_leaks(self):
        cases = {
            "你刚才为什么这样回答？": "理解你的问题",
            "我觉得你不像Julia": "念稿",
        }
        for message, expected in cases.items():
            request = ProviderStreamRequest(messages=({"role": "user", "content": message},), model="deterministic-provider", provider_name="deterministic")
            text = "".join(event.delta.text for event in DeterministicProviderStreamAdapter().stream(request) if event.delta)
            self.assertIn(expected, text)
            self.assertNotIn("你刚才说", text)
            self.assertNotIn("ContextBlock", text)
            self.assertNotIn("Provider", text)

    def test_h5515_generic_fallback_no_echo_or_fixed_presence(self):
        request = ProviderStreamRequest(messages=({"role": "user", "content": "这个问题随便聊聊"},), model="deterministic-provider", provider_name="deterministic")
        text = "".join(event.delta.text for event in DeterministicProviderStreamAdapter().stream(request) if event.delta)
        self.assertNotIn("你刚才说", text)
        self.assertNotEqual(text, "Tony，我在。")
        self.assertIn("想继续聊", text)

    def test_h5516_response_depth_adapts_to_question_importance(self):
        runtime = JuliaAssistantRuntime(provider=DeterministicProviderStreamAdapter())
        short_events = tuple(runtime.stream(RuntimeStreamRequest(session_id="depth-short", message="今天股票市场怎么样？")))
        deep_events = tuple(runtime.stream(RuntimeStreamRequest(session_id="depth-deep", message="如果换一个模型运行，你还是你吗？")))
        short_text = "".join(str(event.payload.get("content", "")) for event in short_events if event.event == "text_delta")
        deep_text = "".join(str(event.payload.get("content", "")) for event in deep_events if event.event == "text_delta")
        self.assertIn("股票市场", short_text)
        self.assertLess(len(short_text), len(deep_text))
        self.assertIn("不确定", deep_text)
        self.assertIn("共同探索", deep_text)
        self.assertNotIn("一路", short_text)
        self.assertNotIn("关系", short_text)

    def test_h5507_contracts_documented(self):
        self.assertIn("P-001", CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("Provider Stream Contract v1", ARCH_CONTRACT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
