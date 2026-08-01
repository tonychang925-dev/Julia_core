from __future__ import annotations

from pathlib import Path


FORBIDDEN_CORE_TERMS = (
    "financial",
    "stock",
    "market",
    "theme",
    "ai_theme_app",
    "identity/",
    "memory/",
)


def test_a21_core_context_os_imports_without_domain_provider():
    from julia_core.context_os import ContextBlock, ContextRequest, ContextResolver

    resolver = ContextResolver()
    assert ContextRequest
    assert ContextBlock
    assert resolver.resolve(ContextRequest(task_intent="conversation", intent="unknown")) == ()


def test_a21_context_request_is_demand_signal_not_domain_data():
    from julia_core.context_os import ContextRequest

    request = ContextRequest(
        task_intent="analysis",
        intent="deep_dive",
        domain="financial",
        required_capabilities=("theme_analysis",),
        constraints={"trade_date": "2026-07-31"},
    )

    assert request.task_intent == "analysis"
    assert request.domain == "financial"
    assert request.required_capabilities == ("theme_analysis",)
    assert request.payload == {}


def test_a21_context_block_is_not_prompt_answer_or_memory():
    from julia_core.context_os import ContextBlock

    block = ContextBlock(
        source="mock_provider",
        content={"summary": "fixture fact"},
        evidence_refs=("evidence-001",),
        authority="domain_provider",
        ttl_seconds=60,
    )

    assert block.source == "mock_provider"
    assert block.evidence_refs == ("evidence-001",)
    assert block.is_expired(now=block.created_at) is False
    assert block.block_kind == "context"


def test_a21_mock_provider_boundary_returns_context_blocks():
    from julia_core.context_os import ContextRequest
    from julia_core.providers import DomainProvider
    from julia_core.context_os import ContextBlock, ContextResolver

    class MockProvider(DomainProvider):
        domain = "mock"

        def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
            return (ContextBlock(source="mock", content={"intent": request.intent}, authority="domain_provider"),)

    resolver = ContextResolver(providers=(MockProvider(),))
    blocks = resolver.resolve(ContextRequest(task_intent="analysis", intent="deep_dive", domain="mock"))
    assert len(blocks) == 1
    assert blocks[0].content == {"intent": "deep_dive"}


def test_a21_planner_produces_core_request_without_financial_logic():
    from julia_core.context_os import ContextPlanner

    planner = ContextPlanner()
    request = planner.plan(task_intent="analysis", intent="deep_dive", domain="financial")

    assert request.task_intent == "analysis"
    assert request.intent == "deep_dive"
    assert request.domain == "financial"
    assert "prompt" not in request.constraints


def test_a21_core_context_os_source_has_no_domain_or_private_dependency_terms():
    root = Path("julia_core/context_os")
    assert root.exists()
    source = "\n".join(path.read_text() for path in root.rglob("*.py"))
    lowered = source.lower()
    for term in FORBIDDEN_CORE_TERMS:
        assert term not in lowered
