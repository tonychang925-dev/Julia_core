from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

import julia_core.public.conversation as conversation
from julia_core.research.anthropic_web import AnthropicWebResearchProvider


ROOT = Path(__file__).resolve().parents[2]


class FakeBridge:
    def __init__(self):
        self.providers = {}
        self.manager = SimpleNamespace(providers=self.providers)
        self.register_calls = []

    def register_provider(self, name, provider):
        existing = self.providers.get(name)
        if existing is not None and existing is not provider:
            raise RuntimeError("different provider rebound")
        self.providers[name] = provider
        self.register_calls.append((name, provider))


class Provider:
    async def health(self):
        return True, "ok"

    async def execute(self, request):
        return {}


@pytest.fixture(autouse=True)
def reset_research_binding(monkeypatch):
    monkeypatch.setattr(conversation, "_research_binding_provider", None)
    monkeypatch.setattr(conversation, "_research_binding_attempted", False)
    monkeypatch.setattr(conversation, "_research_binding_error", None)
    yield


def install_factory(monkeypatch, provider, calls=None):
    if calls is None:
        calls = []

    def factory():
        calls.append("construct")
        return provider

    monkeypatch.setattr(
        "julia_core.research.anthropic_web."
        "AnthropicWebResearchProviderFactory.from_environment",
        staticmethod(factory),
    )
    return calls


def test_canonical_research_binding_constructs_once_and_verifies_identity(monkeypatch):
    bridge = FakeBridge()
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.get_capability_bridge",
        lambda: bridge,
    )
    provider = Provider()
    calls = install_factory(monkeypatch, provider)

    conversation._ensure_research_provider_binding()
    conversation._ensure_research_provider_binding()

    assert calls == ["construct"]
    assert bridge.providers["research"] is provider
    assert conversation._research_binding_provider is provider
    assert bridge.register_calls == [("research", provider)]


def test_missing_credential_leaves_research_unbound_and_retries_never_occur(monkeypatch):
    bridge = FakeBridge()
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.get_capability_bridge",
        lambda: bridge,
    )
    calls = install_factory(monkeypatch, None)

    conversation._ensure_research_provider_binding()
    conversation._ensure_research_provider_binding()

    assert calls == ["construct"]
    assert "research" not in bridge.providers
    assert conversation._research_binding_attempted is True
    assert conversation._research_binding_error is None


def test_prebound_foreign_research_namespace_fails_closed(monkeypatch):
    bridge = FakeBridge()
    bridge.providers["research"] = object()
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.get_capability_bridge",
        lambda: bridge,
    )

    with pytest.raises(conversation.CoreConversationConfigurationError):
        conversation._ensure_research_provider_binding()

    assert conversation._research_binding_error is not None


def test_foreign_research_binding_after_optional_failure_fails_closed(monkeypatch):
    bridge = FakeBridge()
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.get_capability_bridge",
        lambda: bridge,
    )
    install_factory(monkeypatch, None)
    conversation._ensure_research_provider_binding()
    bridge.providers["research"] = object()

    with pytest.raises(conversation.CoreConversationConfigurationError):
        conversation._ensure_research_provider_binding()


def test_research_binding_is_process_safe_under_concurrent_ingress(monkeypatch):
    bridge = FakeBridge()
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.get_capability_bridge",
        lambda: bridge,
    )
    provider = Provider()
    calls = install_factory(monkeypatch, provider)
    started = threading.Event()
    release = threading.Event()

    def factory():
        calls.append("construct")
        started.set()
        assert release.wait(timeout=2)
        return provider

    monkeypatch.setattr(
        "julia_core.research.anthropic_web."
        "AnthropicWebResearchProviderFactory.from_environment",
        staticmethod(factory),
    )
    threads = [threading.Thread(target=conversation._ensure_research_provider_binding) for _ in range(2)]
    threads[0].start()
    assert started.wait(timeout=2)
    threads[1].start()
    release.set()
    for thread in threads:
        thread.join(timeout=2)

    assert len(calls) == 1
    assert bridge.providers["research"] is provider


def test_public_ingress_binds_market_and_research_before_session(monkeypatch, tmp_path):
    order = []

    class FakeRuntime:
        def __init__(self, repository):
            order.append("runtime")

    class FakeSession:
        def __init__(self, provider=None):
            order.append("session")

    monkeypatch.setattr(conversation, "ConversationRuntime", FakeRuntime)
    monkeypatch.setattr(conversation, "JuliaSession", FakeSession)
    monkeypatch.setattr(
        "julia_core.providers.core_cognition._get_cognition_provider",
        lambda _name: object(),
    )
    monkeypatch.setattr(
        conversation,
        "_ensure_market_public_binding",
        lambda: order.append("market"),
    )
    monkeypatch.setattr(
        conversation,
        "_ensure_research_provider_binding",
        lambda: order.append("research"),
    )

    ingress = conversation.CoreConversationIngress(
        conversation.CoreConversationConfig(tmp_path / "conversations")
    )

    assert ingress._composition_error is None
    assert order == ["runtime", "market", "research", "session"]


def test_missing_research_credential_does_not_fail_core_ingress(monkeypatch, tmp_path):
    bridge = FakeBridge()
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.get_capability_bridge",
        lambda: bridge,
    )
    monkeypatch.setattr(conversation, "ConversationRuntime", lambda repository: object())
    monkeypatch.setattr(conversation, "JuliaSession", lambda provider=None: object())
    monkeypatch.setattr(
        "julia_core.providers.core_cognition._get_cognition_provider",
        lambda _name: object(),
    )
    monkeypatch.setattr(conversation, "_ensure_market_public_binding", lambda: None)
    install_factory(monkeypatch, None)

    ingress = conversation.CoreConversationIngress(
        conversation.CoreConversationConfig(tmp_path / "conversations")
    )

    assert ingress._composition_error is None
    assert "research" not in bridge.providers


def test_canonical_research_composition_has_no_legacy_web_reachability():
    composition = (ROOT / "julia_core" / "public" / "conversation.py").read_text()
    research_component = (
        ROOT / "julia_core" / "research" / "anthropic_web.py"
    ).read_text()
    forbidden = (
        "web_provider",
        "web_tools",
        "WebSearchEngine",
        "DuckDuckGoProvider",
        "SerpAPIProvider",
        "WebFetchTool",
    )

    for source in (composition, research_component):
        for marker in forbidden:
            assert marker not in source


def test_missing_credential_research_capability_remains_provider_not_found(monkeypatch):
    from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    execution = bridge.execute_tool_typed(
        '{"name":"research.web.query","arguments":{"query":"robotics catalysts"}}'
    )

    assert execution.tool_result.status.value == "unavailable"
    assert execution.tool_result.error["code"] == "provider_not_found"
    assert execution.tool_result.structured_output == {}
    assert "research" not in bridge.manager.providers
