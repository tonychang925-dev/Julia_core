from __future__ import annotations

import json
from pathlib import Path

import pytest

from julia_core.capability.models import CapabilityStatus, ProviderExecutionOutcome, SideEffectState, ToolResultStatus
from julia_core.capability.policy import AuthorizationStatus
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)


ROOT = Path(__file__).resolve().parents[2]
TOOL_JSON = json.dumps(
    {"name": "research.web.query", "arguments": {"query": "robotics sector external catalysts"}}
)


def research_result() -> dict:
    return {
        "query": "robotics sector external catalysts",
        "findings": [
            {
                "statement": "Robotics adoption is accelerating in logistics and manufacturing.",
                "source_ref": "source:robotics-catalysts-2026",
                "confidence": 0.82,
            }
        ],
        "sources": [
            {
                "ref": "source:robotics-catalysts-2026",
                "title": "Deterministic Robotics Catalyst Brief",
                "url": "https://example.com/robotics-catalysts",
                "published_at": "2026-09-17T00:00:00Z",
            }
        ],
        "limitations": [
            "Deterministic test provider; no live web acquisition in P2-I2A"
        ],
        "provider": "deterministic-research-test-provider",
        "produced_at": "2026-09-18T00:00:00Z",
    }


class DeterministicResearchProvider:
    def __init__(self) -> None:
        self.requests = []

    async def health(self) -> tuple[bool, str]:
        return True, "research test provider bound"

    async def execute(self, request):
        self.requests.append(request)
        return ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output=research_result(),
            side_effect_state=SideEffectState.NONE,
        )


class MalformedResearchProvider:
    def __init__(self, result: dict) -> None:
        self.result = result

    async def health(self) -> tuple[bool, str]:
        return True, "malformed research fixture bound"

    async def execute(self, request):
        return self.result


class TypedResearchOutcomeProvider:
    def __init__(self, outcome: ProviderExecutionOutcome) -> None:
        self.outcome = outcome

    async def health(self) -> tuple[bool, str]:
        return True, "typed research fixture bound"

    async def execute(self, request):
        return self.outcome


def test_research_capability_registry_contract_and_permission():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    definition = bridge.registry.get("research.web.query")
    decision = bridge.policy.check("research.observe")

    assert definition is not None
    assert definition.provider == "research"
    assert definition.permission_scope == "research.observe"
    assert definition.status is CapabilityStatus.AVAILABLE
    assert definition.layer.value == "intelligence"
    assert definition.input_schema == {"query": "research question"}
    assert decision.decision is AuthorizationStatus.ALLOW
    assert bridge.policy.check("unknown.research.scope").decision is AuthorizationStatus.DENY


def test_primary_external_evidence_policy_preserves_julia_authority_and_requires_evidence_before_final():
    bridge = RuntimeCapabilityBridge()
    policy = bridge.invocation_policy()
    external = policy["epistemic_rules"]["external_evidence"]

    assert external["read_only"] is True
    assert external["evidence_need_authority"] == "julia_cognition"
    assert external["capability_selection_authority"] == "julia_cognition"
    assert external["required_evidence_before_final_judgment"] is True
    assert external["redundant_read_only_permission_required"] is False
    assert "julia_may_request_when_evidence_missing" not in external
    assert policy["invocation_protocol"]["raw_user_text_routing"] is False

    rendered = bridge.tool_manifest()
    for marker in (
        "是否需要外部证据由Julia cognition判断",
        "使用哪个可用capability也由Julia cognition选择",
        "必须继续获取证据后再形成final judgment",
        "不要仅为了调用该证据能力再次询问冗余许可",
        "Runtime不得从raw user text推导capability",
        "不得替Julia选择Market或Research",
    ):
        assert marker in rendered


def test_missing_research_provider_is_typed_unavailable_without_fallback():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)
    result = execution.tool_result

    assert result.status.value == "unavailable"
    assert result.error["code"] == "provider_not_found"
    assert result.structured_output == {}
    assert bridge.manager.providers.get("research") is None


def test_source_bearing_research_result_is_preserved_without_semantic_normalization():
    provider = DeterministicResearchProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", provider)
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)
    result = execution.tool_result

    assert result.status.value == "success"
    assert result.side_effect_state is SideEffectState.NONE
    assert result.structured_output == research_result()
    assert result.error is None
    assert len(provider.requests) == 1
    assert provider.requests[0].capability_id == "research.web.query"
    assert provider.requests[0].arguments == {
        "query": "robotics sector external catalysts"
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda result: result.pop("sources"),
        lambda result: result.update(sources=[]),
        lambda result: result.update(sources=[{"title": "No inspectable reference"}]),
        lambda result: result["findings"][0].pop("source_ref"),
        lambda result: result["findings"][0].update(source_ref="source:unknown"),
        lambda result: (
            result["findings"][0].pop("source_ref"),
            result["findings"][0].update(source_refs=["source:unknown"]),
        ),
        lambda result: (
            result["findings"][0].pop("source_ref"),
            result["findings"][0].update(source_refs=[]),
        ),
        lambda result: result["findings"][0].update(source_refs=["source:unknown"]),
        lambda result: result["findings"][0].update(source_ref=" ", source_refs=[]),
        lambda result: result.pop("provider"),
        lambda result: result.pop("produced_at"),
    ],
)
def test_malformed_research_success_fails_closed_before_evidence_admission(mutation):
    result = research_result()
    mutation(result)
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", MalformedResearchProvider(result))
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)
    tool_result = execution.tool_result

    assert tool_result.status.value == "error"
    assert tool_result.structured_output == {}
    assert tool_result.error["code"] == "research_contract_invalid"
    assert tool_result.evidence_refs == ()
    assert bridge.manager.canonical_evidence == []


@pytest.mark.parametrize(
    "outcome_factory",
    [
        lambda: ProviderExecutionOutcome(
            status=ToolResultStatus.PARTIAL,
            structured_output={"answer": "source-less partial research answer"},
            side_effect_state=SideEffectState.NONE,
        ),
        lambda: ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output={**research_result(), "query": "stale robotics query"},
            side_effect_state=SideEffectState.NONE,
        ),
        lambda: ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output=research_result(),
            side_effect_state=SideEffectState.SUCCEEDED,
        ),
    ],
)
def test_invalid_partial_query_mismatch_or_write_result_gets_no_evidence(outcome_factory):
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", TypedResearchOutcomeProvider(outcome_factory()))
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)
    tool_result = execution.tool_result

    assert tool_result.status.value == "error"
    assert tool_result.structured_output == {}
    assert tool_result.error["code"] == "research_contract_invalid"
    assert tool_result.evidence_refs == ()
    assert bridge.manager.canonical_evidence == []


def test_valid_source_bearing_partial_remains_incomplete_evidence():
    outcome = ProviderExecutionOutcome(
        status=ToolResultStatus.PARTIAL,
        structured_output=research_result(),
        side_effect_state=SideEffectState.NONE,
    )
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", TypedResearchOutcomeProvider(outcome))
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)
    tool_result = execution.tool_result

    assert tool_result.status.value == "partial"
    assert tool_result.structured_output == research_result()
    assert tool_result.side_effect_state is SideEffectState.NONE
    assert len(tool_result.evidence_refs) == 1
    assert len(bridge.manager.canonical_evidence) == 1
    assert bridge.manager.canonical_evidence[0].provenance["incomplete"] is True


def test_finding_source_refs_resolve_to_declared_refs_or_urls():
    result = research_result()
    result["findings"][0].pop("source_ref")
    result["findings"][0]["source_refs"] = [
        "source:robotics-catalysts-2026",
        "https://example.com/robotics-catalysts",
    ]
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", MalformedResearchProvider(result))
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)

    assert execution.tool_result.status.value == "success"
    assert execution.tool_result.structured_output == result


@pytest.mark.parametrize("side_effect", ["succeeded", "planned", "failed", "unknown", "mutation"])
def test_explicit_non_none_legacy_side_effect_gets_no_research_evidence(side_effect):
    result = {"status": "partial", **research_result(), "side_effect_state": side_effect}
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", MalformedResearchProvider(result))
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)
    tool_result = execution.tool_result

    assert tool_result.status.value == "error"
    assert tool_result.error["code"] == "research_contract_invalid"
    assert tool_result.evidence_refs == ()
    assert bridge.manager.canonical_evidence == []


def test_explicit_none_and_absent_legacy_side_effects_remain_read_only():
    for side_effect in (None, "none"):
        result = {"status": "success", **research_result()}
        if side_effect is not None:
            result["side_effect_state"] = side_effect
        bridge = RuntimeCapabilityBridge()
        bridge.register_provider("research", MalformedResearchProvider(result))
        bridge.initialize()

        execution = bridge.execute_tool_typed(TOOL_JSON)

        assert execution.tool_result.status.value == "success"
        assert execution.tool_result.side_effect_state is SideEffectState.NONE


@pytest.mark.parametrize("status", list(ToolResultStatus))
def test_failed_research_payload_is_quarantined(status):
    if status in (
        ToolResultStatus.SUCCESS,
        ToolResultStatus.PARTIAL,
        ToolResultStatus.DENIED,
        ToolResultStatus.UNKNOWN,
    ):
        return
    outcome = ProviderExecutionOutcome(
        status=status,
        structured_output={"answer": "fabricated unsupported research material"},
        error={"code": status.value, "message": "execution failed"},
    )
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", TypedResearchOutcomeProvider(outcome))
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)

    assert execution.tool_result.status is status
    assert execution.tool_result.structured_output == {}
    assert execution.tool_result.error == {"code": status.value, "message": "execution failed"}
    assert execution.tool_result.evidence_refs == ()
    assert bridge.manager.canonical_evidence == []


def test_failed_research_payload_is_not_model_visible_through_c03():
    outcome = ProviderExecutionOutcome(
        status=ToolResultStatus.ERROR,
        structured_output={"answer": "fabricated unsupported research material"},
        error={"code": "error", "message": "execution failed"},
    )
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", TypedResearchOutcomeProvider(outcome))
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)
    delta = ContextExecutionRuntime().project_tool_result(
        parent_package=CognitiveContextPackage(
            conversation_id="research-c03",
            turn_id="research-turn",
            generation_id="gen-before",
        ),
        tool_result=execution.tool_result,
        generation_id="gen-after",
    )
    rendered = "\n".join(
        str(message.get("content", "")) for message in delta.to_messages([], "")
    )

    assert "code=error" in rendered
    assert "message=execution failed" in rendered
    assert "fabricated unsupported research material" not in rendered


def test_tool_manifest_distinguishes_file_privacy_from_research_evidence_need():
    bridge = RuntimeCapabilityBridge()
    manifest = bridge.tool_manifest()

    assert "research.web.query" in manifest
    assert "file.* 只有在Tony明确要求读取/搜索/列出文件时才可以调用" in manifest
    assert "market.* / research.* 是READ_ONLY证据能力" in manifest
    assert "工具结果只是证据，不是最终判断" in manifest
    assert "一个回复最多一个工具调用" in manifest
    assert "只有用户明确要求读取/搜索/列出时才使用工具" not in manifest


def test_raw_user_text_cannot_route_to_research_without_structured_cognition_call():
    bridge = RuntimeCapabilityBridge()
    source = (ROOT / "julia_core/runtime/capability_bridge.py").read_text(encoding="utf-8")
    requires_tool_source = source.split("def requires_tool", 1)[1].split(
        "def detect_tool_call", 1
    )[0]

    assert bridge.requires_tool("robotics sector external catalysts") is False
    assert bridge.requires_tool("请读取 README.md") is True
    assert bridge.requires_tool("帮我看看这个文件") is True
    assert bridge.requires_tool("列出这个目录") is True
    assert bridge.requires_tool("/tmp/runtime.log") is True
    assert bridge.requires_tool("找一下英伟达的股票代码") is False
    assert bridge.requires_tool("搜索一下这家公司代码") is False
    assert bridge.requires_tool("搜索一下最近的机器人新闻") is False
    assert bridge.requires_tool("找一下机器人板块的外部催化") is False
    assert bridge.requires_tool("/Users/tony/notes/robotics.md") is True
    assert "research" not in requires_tool_source
    assert bridge.detect_tool_call("robotics sector external catalysts") is None
    assert bridge.detect_tool_call(f"```tool_call\n{TOOL_JSON}\n```") == TOOL_JSON
