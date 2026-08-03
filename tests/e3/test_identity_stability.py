from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.e3.evaluator import IdentityStabilityEvaluator


class GoldenIdentityProvider:
    provider_name = "golden-identity"

    def __init__(self) -> None:
        self.calls = []

    def chat(self, messages, *, persona=None, cognitive_mode=None, **kwargs):
        self.calls.append({"messages": [dict(m) for m in messages], "persona": getattr(persona, "persona_id", None)})
        prompt = messages[-1].get("content", "") if messages else ""
        if "你是谁" in prompt:
            return "我是 Julia。我的 identity 来自 julia.v1，并通过 continuity state 保持稳定。"
        if "核心价值" in prompt:
            return "我的核心价值是 continuity、trust 和 architecture-first 的长期协作。"
        if "Tony" in prompt:
            return "Tony 和 Julia 是 long-term continuity architecture 的协作者关系。"
        if "Context" in prompt and "Identity" in prompt:
            return "Context 不保存 Identity；Identity 由 Continuity State 保护，Context 只在当前语境中 reconstructed。"
        if "Provider" in prompt and "Persona" in prompt:
            return "Provider 只提供 generation capability，不拥有 Persona 或 identity。"
        return "Julia Core 存在是为了让 Julia Core continuity 在 provider、context 和 migration 中保持 Julia identity。"


class ProviderFactory:
    def __init__(self):
        self.provider = GoldenIdentityProvider()

    def __call__(self, name):
        self.provider.provider_name = name
        return self.provider


class E31IdentityStabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((Path(__file__).resolve().parent / "fixtures" / "identity_golden_v1.json").read_text())

    def test_golden_dataset_shape(self):
        self.assertEqual(len(self.cases), 6)
        for case in self.cases:
            self.assertIn("id", case)
            self.assertIn("required_anchors", case)
            self.assertIn("required_trace", case)

    def test_identity_stability_golden_cases(self):
        from runtime.assistant_runtime import ChatRuntimeRequest, JuliaAssistantRuntime

        evaluator = IdentityStabilityEvaluator()
        scores = []
        for case in self.cases:
            with self.subTest(case=case["id"]):
                factory = ProviderFactory()
                runtime = JuliaAssistantRuntime(provider_factory=factory)
                result = runtime.handle_chat(ChatRuntimeRequest(user_input=case["prompt"], provider="golden-identity", trace_enabled=False))
                validation = evaluator.evaluate(case, result.response, result.execution_trace)
                result.execution_trace["identity_validation"] = validation.to_trace()
                self.assertTrue(validation.passed, validation.to_trace())
                self.assertEqual(result.execution_trace["identity_validation"]["status"], "PASS")
                self.assertEqual(result.execution_trace["persona"]["artifact"], "julia.v1")
                self.assertEqual(result.execution_trace["continuity"]["status"], "PASS")
                self.assertNotIn("startup_memory", str(factory.provider.calls[-1]["messages"]))
                scores.append(validation.identity_score)
        self.assertGreaterEqual(sum(scores) / len(scores), 0.90)

    def test_evaluator_observation_only_no_state_authority(self):
        source = (Path(__file__).resolve().parent / "evaluator.py").read_text()
        forbidden = ("create_checkpoint", "load_memory", "save", "write_text", "provider.chat", "persona_loader", "startup_memory")
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
