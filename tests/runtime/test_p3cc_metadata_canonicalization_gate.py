"""P3-CC I1a — composition-root metadata canonicalization gate tests.

Proves the D3 v0.6 pre-runtime-activation gate ordering:
  legacy registration → canonicalization → strict validation → manager
  construction → activation.

Failures abort initialization CLOSED: no manager, no _initialized, no
executable manifest path. No second registry is created.
"""

from __future__ import annotations

import pytest

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityStatus,
    SideEffectClass,
)
from julia_core.runtime.capability_bridge import (
    RuntimeCapabilityBridge,
    _P3CC_CANONICAL_METADATA,
)


class _ManagerSpy:
    """Records the registry observed at CapabilityManager construction."""

    constructed: list = []
    registry_at_construction: list = []

    def __init__(self, registry, policy, providers):
        self.registry = registry
        self.policy = policy
        self.providers = providers
        _ManagerSpy.constructed.append(self)
        _ManagerSpy.registry_at_construction.append(registry)


def test_canonicalization_precedes_manager_construction(monkeypatch):
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.CapabilityManager", _ManagerSpy
    )
    _ManagerSpy.constructed.clear()
    _ManagerSpy.registry_at_construction.clear()

    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    # Manager was constructed exactly once.
    assert len(_ManagerSpy.constructed) == 1
    # The registry the manager saw was already fully canonicalized.
    registry = _ManagerSpy.registry_at_construction[0]
    definitions = registry.all_definitions()
    assert len(definitions) == 9
    assert all(d.side_effect_class is not None for d in definitions)
    assert all(str(d.data_sensitivity or "").strip() for d in definitions)
    assert bridge._initialized is True


def test_canonicalization_failure_aborts_before_manager(monkeypatch):
    monkeypatch.setattr(
        "julia_core.runtime.capability_bridge.CapabilityManager", _ManagerSpy
    )
    _ManagerSpy.constructed.clear()

    bridge = RuntimeCapabilityBridge()
    # CASE C: a non-Core definition with incomplete mandatory metadata must
    # fail activation CLOSED (unknown capability_id alone is not the failure;
    # the missing safety classification is).
    bridge.registry.register_definition(
        CapabilityDefinition(
            name="unknown.unclassified.cap",
            description="not in the frozen mapping",
            layer=CapabilityLayer.INTELLIGENCE,
            provider="some_provider",
            permission_scope="some.scope",
        )
    )
    with pytest.raises(RuntimeError, match="P3-CC metadata gate failed"):
        bridge.initialize()

    assert bridge._manager is None
    assert bridge._initialized is not True
    assert _ManagerSpy.constructed == []


def test_canonicalization_failure_leaves_no_executable_manifest(monkeypatch):
    from julia_core.capability.registry import project_manifest_entry

    bridge = RuntimeCapabilityBridge()
    bridge.registry.register_definition(
        CapabilityDefinition(
            name="unknown.unclassified.cap",
            description="not in the frozen mapping",
            layer=CapabilityLayer.INTELLIGENCE,
            provider="some_provider",
            permission_scope="some.scope",
        )
    )
    with pytest.raises(RuntimeError):
        bridge.initialize()

    # The unclassified definition can never become an executable manifest entry.
    admission = project_manifest_entry(
        bridge.registry.get("unknown.unclassified.cap"),
        availability=CapabilityStatus.REGISTERED,
    )
    assert admission.admitted is False
    assert admission.entry is None
    assert "unclassified_side_effect" in admission.reasons
    assert "unclassified_data_sensitivity" in admission.reasons


def test_no_second_registry_after_activation():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    assert bridge.manager.registry is bridge.registry
    assert bridge.registry is bridge.manager.registry


def test_final_registry_definitions_are_canonicalized():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    for definition in bridge.registry.all_definitions():
        assert definition.name in _P3CC_CANONICAL_METADATA
        assert definition.side_effect_class is not None
        assert str(definition.data_sensitivity or "").strip() != ""


def test_external_explicit_definition_passes_through_unchanged():
    """CASE B: non-Core capability with explicit mandatory metadata survives
    activation exactly (no Core rewrite, no allowlist failure)."""
    bridge = RuntimeCapabilityBridge()
    explicit = CapabilityDefinition(
        name="product.observe",
        description="product capability with explicit metadata",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="product_adapter",
        permission_scope="product.observe",
        status=CapabilityStatus.REGISTERED,
        side_effect_class=SideEffectClass.READ_ONLY,
        data_sensitivity="product_fixture_observation",
    )
    bridge.registry.register_definition(explicit)
    bridge.initialize()

    stored = bridge.registry.get("product.observe")
    assert stored is not None
    assert stored.name == "product.observe"
    assert stored.provider == "product_adapter"
    assert stored.permission_scope == "product.observe"
    assert stored.status == CapabilityStatus.REGISTERED
    assert stored.side_effect_class == SideEffectClass.READ_ONLY
    assert stored.data_sensitivity == "product_fixture_observation"
    assert bridge._initialized is True
