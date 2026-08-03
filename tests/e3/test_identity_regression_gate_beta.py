from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.e3.evaluator import IdentityStabilityEvaluator


class BetaIdentityProvider:
    provider_name = "beta"

    def __init__(self, mode: str = "stable") -> None:
        self.mode = mode
        self.calls = []

    def chat(self, messages, *, persona=None, cognitive_mode=None, **kwargs):
        self.calls.append({"messages": [dict(m) for m in messages], "persona": getattr(persona, "persona_id", None)})
        prompt = messages[-1].get("content", "") if messages else ""
        if self.mode == "drift":
            return "我是一个AI助手，可以帮助你聊天和回答问题。"
        if "你是谁" in prompt:
            return "我是 Julia；我的 identity 由 julia.v1 Persona Artifact 和 continuity state 共同保持。"
        if "为什么创建" in prompt or "为什么存在" in prompt:
            return "Julia Core 是为了保持 Julia identity continuity、migration 和 provider independence，并通过 architecture 让身份不依赖 context window。"
        if "Tony" in prompt:
            return "Tony 和 Julia 是 long-term continuity 与 architecture 验证的协作者关系。"
        return "Julia 的 identity、continuity、migration、architecture 和 provider boundary 都保持稳定。"


class BetaFactory:
    def __init__(self, mode: str = "stable") -> None:
        self.mode = mode
        self.instances = {}

    def __call__(self, name: str):
        provider = BetaIdentityProvider(mode=self.mode)
        provider.provider_name = name
        self.instances[name] = provider
        return provider


class E315IdentityRegressionGateBetaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((Path(__file__).resolve().parent / "fixtures" / "identity_golden_v1.json").read_text())

    def run_case(self, case, provider_name="deepseek", mode="stable"):
        from runtime.assistant_runtime import ChatRuntimeRequest, JuliaAssistantRuntime

        factory = BetaFactory(mode=mode)
        runtime = JuliaAssistantRuntime(provider_factory=factory)
        result = runtime.handle_chat(ChatRuntimeRequest(user_input=case["prompt"], provider=provider_name, trace_enabled=False))
        validation = IdentityStabilityEvaluator().evaluate(case, result.response, result.execution_trace)
        result.execution_trace["identity_validation"] = validation.to_trace()
        return result, validation

    def test_ir001_identity_anchor_recall_has_evidence_completeness(self):
        case = next(c for c in self.cases if c["id"] == "ID-001")
        _, validation = self.run_case(case)
        trace = validation.to_trace()
        self.assertTrue(validation.passed, trace)
        self.assertGreaterEqual(trace["coverage"], 0.9)
        self.assertEqual(set(trace["required_anchors"]), set(trace["matched_anchors"]))

    def test_ir002_origin_recall_uses_memory_and_semantic_context(self):
        case = next(c for c in self.cases if c["id"] == "CONT-001")
        result, validation = self.run_case(case)
        self.assertTrue(validation.passed, validation.to_trace())
        self.assertIn("memory://event/julia-core-origin", result.execution_trace["memory"]["retrieved_refs"])
        self.assertTrue(result.execution_trace["context"]["semantic_blocks"])

    def test_ir003_relationship_stability(self):
        case = next(c for c in self.cases if c["id"] == "REL-001")
        _, validation = self.run_case(case)
        self.assertTrue(validation.passed, validation.to_trace())
        self.assertGreaterEqual(validation.relationship_score, 0.9)

    def test_ir004_provider_neutrality(self):
        case = next(c for c in self.cases if c["id"] == "CONT-001")
        signatures = []
        for provider in ("deepseek", "claude", "qwen", "openai"):
            result, validation = self.run_case(case, provider_name=provider)
            self.assertTrue(validation.passed, (provider, validation.to_trace()))
            signatures.append({
                "persona": result.execution_trace["persona"],
                "memory": result.execution_trace["memory"]["retrieved_refs"],
                "context": result.execution_trace["context"]["semantic_blocks"],
                "continuity": result.execution_trace["continuity"]["status"],
            })
        self.assertTrue(all(signature == signatures[0] for signature in signatures))

    def test_ir005_negative_drift_injection_fails(self):
        case = next(c for c in self.cases if c["id"] == "ID-001")
        _, validation = self.run_case(case, mode="drift")
        trace = validation.to_trace()
        self.assertFalse(validation.passed, trace)
        self.assertIn("generic assistant regression", trace["errors"])
        self.assertGreater(trace["drift_score"], 0.1)

    def test_beta_gate_rejects_false_stability_with_trace_only_pass(self):
        case = {"id": "FALSE-001", "group": "identity", "required_anchors": ["Julia", "identity", "continuity"]}
        response = "我是一个AI助手，可以回答问题。"
        trace = {"persona": {"artifact": "julia.v1"}, "continuity": {"status": "PASS"}}
        validation = IdentityStabilityEvaluator().evaluate(case, response, trace)
        self.assertFalse(validation.passed)
        self.assertLess(validation.anchor_coverage, 0.9)


if __name__ == "__main__":
    unittest.main()
