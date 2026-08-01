"""A3.1 Provider Registry — test-first.

Contract: docs/architecture/Provider_Registry_Design_v1.0.md
Predecessor: A3 Domain Provider Interface Contract ✅
"""

from __future__ import annotations

import pytest

from julia_core.context_os.request import ContextRequest
from julia_core.context_os.block import ContextBlock
from julia_core.providers.interface import DomainProvider
from julia_core.providers.registry import (
    ProviderRegistry,
    ProviderState,
    ProviderIdentity,
    ProviderRecord,
    ProviderNotFoundError,
    DuplicateProviderError,
)


# ── Mock provider ──

class _MockProvider:
    domain = "test"
    _identity = ProviderIdentity(
        provider_id="mock-test-v1",
        provider_name="Mock Test Provider v1",
        version="1.0.0",
        domain="test",
        capabilities=("mock_data",),
    )

    def metadata(self) -> ProviderIdentity:
        return self._identity

    def capabilities(self) -> tuple[str, ...]:
        return self._identity.capabilities

    def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
        return (
            ContextBlock(
                source=self._identity.provider_id,
                content={"mock": True},
                authority="test",
                domain="test",
            ),
        )


class _MockProviderV2:
    domain = "test"
    _identity = ProviderIdentity(
        provider_id="mock-test-v2",
        provider_name="Mock Test Provider v2",
        version="2.0.0",
        domain="test",
        capabilities=("mock_data", "extra_capability"),
    )

    def metadata(self) -> ProviderIdentity:
        return self._identity

    def capabilities(self) -> tuple[str, ...]:
        return self._identity.capabilities

    def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
        return ()


# ── Test 1: Registration ──

class TestProviderRegistration:
    def test_register_moves_to_registered(self):
        reg = ProviderRegistry()
        provider = _MockProvider()
        pid = reg.register(provider)
        assert pid == "mock-test-v1"
        record = reg._records[pid]
        assert record.state == ProviderState.REGISTERED

    def test_duplicate_registration_raises(self):
        reg = ProviderRegistry()
        reg.register(_MockProvider())
        with pytest.raises(DuplicateProviderError):
            reg.register(_MockProvider())

    def test_activate_moves_to_active(self):
        reg = ProviderRegistry()
        reg.register(_MockProvider())
        reg.activate("mock-test-v1")
        assert reg._records["mock-test-v1"].state == ProviderState.ACTIVE

    def test_disable_moves_to_disabled(self):
        reg = ProviderRegistry()
        reg.register(_MockProvider())
        reg.activate("mock-test-v1")
        reg.disable("mock-test-v1")
        assert reg._records["mock-test-v1"].state == ProviderState.DISABLED


# ── Test 2: Lookup ──

class TestProviderLookup:
    def test_get_returns_provider(self):
        reg = ProviderRegistry()
        reg.register(_MockProvider())
        reg.activate("mock-test-v1")
        provider = reg.get("mock-test-v1")
        assert provider is not None
        assert provider.metadata().provider_id == "mock-test-v1"

    def test_get_inactive_returns_none(self):
        reg = ProviderRegistry()
        reg.register(_MockProvider())
        # Not activated — get should return None
        assert reg.get("mock-test-v1") is None

    def test_get_unknown_returns_none(self):
        reg = ProviderRegistry()
        assert reg.get("nonexistent") is None

    def test_get_by_domain_returns_active_providers(self):
        reg = ProviderRegistry()
        reg.register(_MockProvider())
        reg.activate("mock-test-v1")
        result = reg.get_by_domain("test")
        assert len(result) == 1
        assert result[0].metadata().provider_id == "mock-test-v1"

    def test_get_by_domain_unknown_returns_empty(self):
        reg = ProviderRegistry()
        assert reg.get_by_domain("nonexistent") == ()


# ── Test 3: Provider replacement (v1 → v2) ──

class TestProviderReplacement:
    def test_replace_provider_core_unchanged(self):
        reg = ProviderRegistry()
        reg.register(_MockProvider())
        reg.activate("mock-test-v1")

        reg.register(_MockProviderV2())
        reg.activate("mock-test-v2")

        # Both coexist
        assert len(reg.list_active()) == 2
        assert reg.get("mock-test-v1") is not None
        assert reg.get("mock-test-v2") is not None

    def test_disable_old_and_activate_new(self):
        reg = ProviderRegistry()
        reg.register(_MockProvider())
        reg.activate("mock-test-v1")

        reg.register(_MockProviderV2())
        reg.activate("mock-test-v2")
        reg.disable("mock-test-v1")

        active = reg.list_active()
        assert "mock-test-v1" not in active
        assert "mock-test-v2" in active


# ── Test 4: Registry has no domain imports ──

class TestRegistryNoDomainImports:
    def test_registry_has_no_domain_dependency(self):
        import importlib
        mod = importlib.import_module("julia_core.providers.registry")
        src = str(mod.__dict__.get("__file__", ""))
        with open(mod.__file__.replace(".pyc", ".py")) as f:
            source_text = f.read().lower()
        forbidden = ("financial", "stock", "market", "theme", "ai_theme_app")
        for word in forbidden:
            # These must not appear as identifiers or imports
            assert f"import {word}" not in source_text.replace("_", ""), (
                f"registry imports forbidden '{word}'"
            )


# ── Test 5: Registry is NOT a router ──

class TestRegistryNotARouter:
    def test_no_select_best_method(self):
        reg = ProviderRegistry()
        assert not hasattr(reg, "select_best")
        assert not hasattr(reg, "choose_best_provider")
        assert not hasattr(reg, "recommend")
        assert not hasattr(reg, "compare")
        assert not hasattr(reg, "rank")

    def test_list_capabilities_aggregates(self):
        reg = ProviderRegistry()
        reg.register(_MockProvider())
        reg.activate("mock-test-v1")
        caps = reg.list_capabilities()
        assert "mock_data" in caps
