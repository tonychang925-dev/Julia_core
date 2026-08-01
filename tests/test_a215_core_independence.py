from __future__ import annotations

from pathlib import Path

from julia_core.context_os import ContextBlock, ContextRequest, ContextResolver
from julia_core.providers import DomainProvider


FORBIDDEN_DEPENDENCIES = (
    "financial",
    "stock",
    "market",
    "theme",
    "ai_theme_app",
    "identity/",
    "memory/",
    "vector",
    "embedding",
    "llm",
)


def test_a215_core_imports_without_any_domain_provider():
    import julia_core.context_os as context_os

    assert context_os.ContextRequest is ContextRequest
    assert context_os.ContextBlock is ContextBlock
    assert context_os.ContextResolver is ContextResolver


def test_a215_empty_domain_environment_resolves_without_domain():
    resolver = ContextResolver()
    request = ContextRequest(task_intent="analysis", intent="deep_dive", domain="financial")

    assert resolver.providers == ()
    assert resolver.resolve(request) == ()


def test_a215_mock_provider_only_uses_provider_interface():
    class MockProvider(DomainProvider):
        domain = "mock"

        def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
            return (
                ContextBlock(
                    source="mock_provider",
                    domain=request.domain,
                    content={"fact": "mock evidence"},
                    evidence_refs=("mock-evidence-001",),
                    authority="domain_provider",
                ),
            )

    resolver = ContextResolver(providers=(MockProvider(),))
    blocks = resolver.resolve(ContextRequest(task_intent="analysis", intent="deep_dive", domain="mock"))

    assert len(blocks) == 1
    assert blocks[0].source == "mock_provider"
    assert blocks[0].evidence_refs == ("mock-evidence-001",)


def test_a215_provider_replacement_does_not_modify_core_context_os():
    class ProviderA(DomainProvider):
        domain = "replaceable"

        def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
            return (ContextBlock(source="provider_a", content={"provider": "A"}, authority="domain_provider"),)

    class ProviderB(DomainProvider):
        domain = "replaceable"

        def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
            return (ContextBlock(source="provider_b", content={"provider": "B"}, authority="domain_provider"),)

    request = ContextRequest(task_intent="analysis", intent="compare", domain="replaceable")

    assert ContextResolver(providers=(ProviderA(),)).resolve(request)[0].content == {"provider": "A"}
    assert ContextResolver(providers=(ProviderB(),)).resolve(request)[0].content == {"provider": "B"}


def test_a215_core_dependency_isolation_scan():
    root = Path("runtime/core")
    source = "\n".join(path.read_text() for path in root.rglob("*.py"))
    lowered = source.lower()

    for forbidden in FORBIDDEN_DEPENDENCIES:
        assert forbidden not in lowered


def test_a215_context_block_lifecycle_is_session_context_not_memory():
    block = ContextBlock(source="mock", content={"short": "lived"}, authority="domain_provider", ttl_seconds=1)

    assert block.block_kind == "context"
    assert block.expires_at is not None
    assert block.is_expired(now=block.created_at) is False
