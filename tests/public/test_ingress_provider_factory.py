"""#237 P1: CoreConversationIngress(provider_factory=...) — explicit dependency
injection of the cognition provider (keyword-only, default = production,
no environment switch). Used by the isolated test brain."""
from __future__ import annotations

import inspect

import pytest

from julia_core.public.conversation import (
    CoreConversationConfig,
    CoreConversationIngress,
    CoreConversationProviderUnavailable,
)


class _Provider:
    def chat(self, messages, cognitive_mode=""):
        return "stub reply"


def test_signature_is_keyword_only_with_a_production_default():
    param = inspect.signature(CoreConversationIngress.__init__).parameters["provider_factory"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY and param.default is None


def test_injected_factory_supplies_the_provider_and_skips_production_composition(tmp_path, monkeypatch):
    def forbidden(*_a, **_k):
        raise AssertionError("production composition must not run when a provider_factory is injected")

    monkeypatch.setattr("julia_core.providers.core_cognition.initialize_production_cognition", forbidden)
    monkeypatch.setattr("julia_core.providers.core_cognition._get_cognition_provider", forbidden)
    monkeypatch.setattr("julia_core.public.conversation._ensure_market_public_binding", forbidden)
    monkeypatch.setattr("julia_core.public.conversation._ensure_claude_client_research_binding", forbidden)
    provider = _Provider()
    calls = []
    ingress = CoreConversationIngress(
        CoreConversationConfig(tmp_path / "data"), provider_factory=lambda: calls.append(1) or provider
    )
    assert ingress._composition_error is None and calls == [1]
    assert ingress._session.provider is provider


def test_default_path_still_composes_the_production_provider(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr("julia_core.providers.core_cognition.initialize_production_cognition", lambda: seen.append("init"))
    monkeypatch.setattr("julia_core.providers.core_cognition._get_cognition_provider", lambda name: seen.append(name) or object())
    monkeypatch.setattr("julia_core.public.conversation._ensure_market_public_binding", lambda: seen.append("market"))
    monkeypatch.setattr("julia_core.public.conversation._ensure_claude_client_research_binding", lambda: seen.append("research"))
    ingress = CoreConversationIngress(CoreConversationConfig(tmp_path / "data"))
    assert ingress._composition_error is None
    assert seen == ["init", "production", "market", "research"]


@pytest.mark.parametrize("factory", [lambda: None, lambda: (_ for _ in ()).throw(RuntimeError("boom"))])
def test_bad_factory_fails_closed(tmp_path, factory):
    ingress = CoreConversationIngress(CoreConversationConfig(tmp_path / "data"), provider_factory=factory)
    assert ingress._composition_error is not None and ingress._session is None


def test_none_provider_is_reported_as_provider_unavailable(tmp_path):
    ingress = CoreConversationIngress(CoreConversationConfig(tmp_path / "data"), provider_factory=lambda: None)
    assert isinstance(ingress._composition_error, CoreConversationProviderUnavailable)
