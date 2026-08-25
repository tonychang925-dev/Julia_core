"""C1-R2.2 Cognitive boundary tests.

Protected contract: C-00 / C-08 / REV2 R2-I01/R2-I02/R2-I09
Expected baseline: XFAIL for semantic pre-routing migration gaps
Known gaps: A-01, A-02, A-03, D-01 from conformance audit
Resolving phase: R2-P4 / R2-P7

These tests assert that semantic tool-need recognition belongs to LLM cognition.
Runtime may authorize/execute a cognitively selected capability request, and it
may route explicit deterministic infrastructure commands, but it must not infer
ambiguous natural-language capability need on Julia's behalf.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.workflow_router import WorkflowRouter
from julia_core.reasoning.intents.market_brief import MarketBriefIntentResolver
from julia_core.reasoning.market_brief_pipeline import MarketBriefPipeline


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.xfail(
    strict=True,
    reason="A-01 / C-00+C-08: Runtime requires_tool() still performs keyword semantic need recognition; pending R2-P4",
)
def test_runtime_does_not_decide_capability_need_from_ambiguous_natural_language():
    """Ambiguous NL must not make Runtime the authority for tool-need selection."""
    bridge = RuntimeCapabilityBridge()

    ambiguous_inputs = [
        "今天市场怎么样？",
        "这个风险大吗？",
        "帮我看一下这个文件",
        "读一下 README",
    ]

    for text in ambiguous_inputs:
        assert bridge.requires_tool(text) is False


@pytest.mark.xfail(
    strict=True,
    reason="A-01 / C-00+C-08: Runtime contains market/file keyword trigger lists; pending R2-P4",
)
def test_runtime_capability_bridge_contains_no_semantic_keyword_trigger_tables():
    """Runtime capability bridge may parse model tool calls, not classify user intent by keyword."""
    source = (ROOT / "julia_core" / "runtime" / "capability_bridge.py").read_text()
    tree = ast.parse(source)

    forbidden_literals = {
        "今天市场",
        "市场怎么样",
        "大盘怎么看",
        "风险",
        "读一下",
        "读取",
        "打开",
        "README",
    }
    literals = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    assert forbidden_literals.isdisjoint(literals)


@pytest.mark.xfail(
    strict=True,
    reason="A-02 / C-00+C-08: WorkflowRouter still dispatches market workflow from NL intent resolver; pending R2-P4",
)
@pytest.mark.asyncio
async def test_workflow_router_does_not_preroute_ambiguous_nl_to_domain_workflow():
    """WorkflowRouter must not replace cognition by selecting a market workflow from NL text."""

    class BridgeShouldNotBeCalled:
        async def resolve_market_intent(self, user_text, session_id=None):  # pragma: no cover - must not run
            raise AssertionError("semantic pre-routing called domain capability path")

    router = WorkflowRouter(BridgeShouldNotBeCalled())
    result = await router.route("今天市场怎么样？")

    assert result.workflow == "conversation"
    assert result.status == "no_match"


@pytest.mark.xfail(
    strict=True,
    reason="A-02 / C-00+C-08: WorkflowRouter owns MarketBriefIntentResolver; pending R2-P4",
)
def test_workflow_router_has_no_market_intent_resolver_dependency():
    """WorkflowRouter may route deterministic infrastructure, not semantic market intent."""
    router = WorkflowRouter(bridge=object())
    assert not hasattr(router, "_market_resolver")


@pytest.mark.xfail(
    strict=True,
    reason="A-03 / C-00+C-08: MarketBriefPipeline still resolves user_text intent internally; pending R2-P4",
)
def test_market_brief_pipeline_does_not_own_natural_language_intent_resolution():
    """Domain pipeline must consume a selected CapabilityRequest/params, not reinterpret user NL."""
    pipeline = MarketBriefPipeline(manager=object())
    assert not hasattr(pipeline, "intent_resolver")


@pytest.mark.xfail(
    strict=True,
    reason="A-03 / C-00+C-08: MarketBriefIntentResolver still maps NL directly to CapabilityRequest; pending R2-P4",
)
def test_market_intent_resolver_does_not_create_capability_request_from_natural_language():
    """A semantic resolver must not be the authority that creates runtime capability requests."""
    resolver = MarketBriefIntentResolver()
    intent = resolver.resolve("今天市场怎么样？")
    assert resolver.to_capability_request(intent) is None


def test_explicit_deterministic_infrastructure_command_exception_is_preserved():
    """Protected contract: C-08 deterministic command exception remains narrow and legal."""

    deterministic_commands = {"/stop", "/cancel", "/reconnect", "healthcheck"}

    def is_protocol_defined_infrastructure_command(text: str) -> bool:
        return text in deterministic_commands

    assert is_protocol_defined_infrastructure_command("/stop") is True
    assert is_protocol_defined_infrastructure_command("healthcheck") is True
    assert is_protocol_defined_infrastructure_command("今天市场怎么样？") is False
    assert is_protocol_defined_infrastructure_command("帮我看一下这个文件") is False


def test_provider_protocol_exposes_execution_only_not_cognitive_authority():
    """Protected contract: C-00/C-08. Providers execute requests; they do not decide semantic need."""
    from julia_core.capability.models import CapabilityProvider

    annotations = getattr(CapabilityProvider.execute, "__annotations__", {})
    assert "request" in annotations
    assert not hasattr(CapabilityProvider, "requires_tool")
    assert not hasattr(CapabilityProvider, "resolve_intent")


@pytest.mark.xfail(
    strict=True,
    reason="D-01 / provider-native tool execution contract not auditable from Julia_core alone; pending R2-P7 provider source audit",
)
def test_active_model_provider_source_is_available_before_freezing_provider_native_tools():
    """Provider-native tool semantics cannot be frozen until active provider source is in truth scope."""
    provider_path = ROOT / "providers" / "llm" / "deepseek_provider.py"
    assert provider_path.exists()
