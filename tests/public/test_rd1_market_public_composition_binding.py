"""RD1 P1-I5: Core composition binds the Market public provider exactly once."""
from __future__ import annotations

import sys
import threading
import time
import types
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import julia_core.public.conversation as conversation


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


@dataclass(frozen=True)
class EventResolveRequest:
    feed_date: str | None = None
    stock_id: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class EventReadRequest:
    event_id: int


@dataclass(frozen=True)
class ProductReadRequest:
    subject_key: str


class FakePublicProvider:
    async def execute(self, capability, request, *, request_id=None, correlation_id=None):
        return {
            "contract_version": "fixture",
            "capability_id": capability,
            "request_id": request_id,
            "correlation_id": correlation_id or "",
            "operation_status": "SUCCESS",
            "data_state": "READY",
            "payload": {"ok": True},
            "provenance": {},
            "failures": [],
            "boundary_identity_ref": "market.public",
            "runtime_observation": None,
            "produced_at": "2026-09-18T00:00:00+00:00",
        }


@pytest.fixture(autouse=True)
def reset_market_binding(monkeypatch):
    monkeypatch.setattr(conversation, "_market_binding_adapter", None)
    monkeypatch.setattr(conversation, "_market_binding_attempted", False)
    monkeypatch.setattr(conversation, "_market_binding_error", None)
    yield


def _install_fake_market_public(monkeypatch, *, factory_impl):
    module = types.ModuleType("market_public")
    module.MarketPublicFactory = factory_impl
    module.EventResolveRequest = EventResolveRequest
    module.EventReadRequest = EventReadRequest
    module.ProductReadRequest = ProductReadRequest
    monkeypatch.setitem(sys.modules, "market_public", module)


def test_market_factory_constructs_once_and_reuses_same_adapter(monkeypatch):
    bridge = FakeBridge()
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.get_capability_bridge",
        lambda: bridge,
    )

    calls = []

    class Factory:
        @staticmethod
        def create():
            calls.append("create")
            return FakePublicProvider()

    _install_fake_market_public(monkeypatch, factory_impl=Factory)

    conversation._ensure_market_public_binding()
    first = bridge.providers["market"]
    conversation._ensure_market_public_binding()
    second = bridge.providers["market"]

    assert calls == ["create"]
    assert first is second
    assert conversation._market_binding_adapter is first
    assert bridge.register_calls == [("market", first)]


def test_market_factory_receives_no_core_database_or_repository_configuration(monkeypatch):
    bridge = FakeBridge()
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.get_capability_bridge",
        lambda: bridge,
    )

    class Factory:
        @staticmethod
        def create(*args, **kwargs):
            assert args == ()
            assert kwargs == {}
            return FakePublicProvider()

    _install_fake_market_public(monkeypatch, factory_impl=Factory)

    conversation._ensure_market_public_binding()

    assert "market" in bridge.providers


def test_missing_market_public_package_leaves_namespace_unbound_without_fake_provider(
    monkeypatch,
):
    bridge = FakeBridge()
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.get_capability_bridge",
        lambda: bridge,
    )
    monkeypatch.delitem(sys.modules, "market_public", raising=False)

    real_import = __import__

    def fail_market_import(name, *args, **kwargs):
        if name == "market_public":
            raise ModuleNotFoundError("market_public unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fail_market_import)

    conversation._ensure_market_public_binding()
    conversation._ensure_market_public_binding()

    assert "market" not in bridge.providers
    assert conversation._market_binding_adapter is None
    assert conversation._market_binding_attempted is True


def test_core_ingress_calls_market_binding_before_session_construction(monkeypatch, tmp_path):
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

    ingress = conversation.CoreConversationIngress(
        conversation.CoreConversationConfig(tmp_path / "conversations")
    )

    assert ingress._composition_error is None
    assert order == ["runtime", "market", "session"]


def test_market_namespace_collision_persists_as_composition_failure(monkeypatch):
    bridge = FakeBridge()
    bridge.providers["market"] = object()
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.get_capability_bridge",
        lambda: bridge,
    )

    class Factory:
        @staticmethod
        def create():
            raise AssertionError("Market factory must not run after namespace collision")

    _install_fake_market_public(monkeypatch, factory_impl=Factory)

    with pytest.raises(conversation.CoreConversationConfigurationError):
        conversation._ensure_market_public_binding()

    # The authority error must be sticky. A later ingress cannot silently
    # continue on the pre-existing provider.
    with pytest.raises(conversation.CoreConversationConfigurationError):
        conversation._ensure_market_public_binding()

    assert conversation._market_binding_adapter is None
    assert conversation._market_binding_error is not None


def test_capability_bridge_singleton_is_not_visible_before_initialize_completes(monkeypatch):
    import julia_core.runtime.capability_bridge as bridge_module

    class SlowBridge:
        def __init__(self):
            self.initialized = False
            self.initialize_started = 0

        def initialize(self):
            if self.initialized:
                return
            self.initialize_started += 1
            time.sleep(0.02)
            self.initialized = True

    monkeypatch.setattr(bridge_module, "_bridge", None)
    monkeypatch.setattr(bridge_module, "RuntimeCapabilityBridge", SlowBridge)

    observed = []
    errors = []

    def worker():
        try:
            bridge = bridge_module.get_capability_bridge()
            observed.append((id(bridge), bridge.initialized))
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert len({bridge_id for bridge_id, _ in observed}) == 1
    assert all(initialized for _, initialized in observed)
    assert bridge_module._bridge.initialize_started == 1
