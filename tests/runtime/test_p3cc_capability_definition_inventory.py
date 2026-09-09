"""P3-CC I1a — production CapabilityDefinition inventory + classification tests.

Mechanically proves that after composition-root canonicalization every
production-reachable CapabilityDefinition carries explicit side_effect_class
and data_sensitivity, and that the frozen 16-row mapping holds.

The provider-first production composition registers 16 definitions
(3 file.* + 11 market.* + research.event.enrich + engineering.code_review).
The provider-absent composition registers 9 (3 file.* + 4 frozen market.* +
research.event.enrich + engineering.code_review). Canonicalization applies to
whatever the single registry actually contains; the frozen mapping table must
cover every production id.
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

BASELINE_IDS = sorted(_P3CC_CANONICAL_METADATA)

EXPECTED_16 = {
    "file.read",
    "file.search",
    "file.list",
    "market.event.resolve",
    "market.event.read",
    "market.snapshot.read",
    "market.alert.query",
    "market.intelligence.observe",
    "market.decision.explain",
    "market.stock.history",
    "market.stock.auction",
    "market.theme.constituents",
    "market.theme.capital",
    "market.regime.read",
    "research.event.enrich",
    "engineering.code_review",
}


def _legacy_def(name: str) -> CapabilityDefinition:
    return CapabilityDefinition(
        name=name,
        description=f"legacy {name}",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="local",
        permission_scope="market.observe",
        status=CapabilityStatus.REGISTERED,
    )


def test_frozen_baseline_mapping_covers_exactly_16_definitions():
    assert len(_P3CC_CANONICAL_METADATA) == 16
    assert set(BASELINE_IDS) == EXPECTED_16


def test_provider_first_composition_canonicalizes_all_16():
    bridge = RuntimeCapabilityBridge()
    # Simulate the provider-first composition surface: every production id is
    # registered as a legacy (unclassified) definition first.
    for capability_id in BASELINE_IDS:
        bridge.registry.register_definition(_legacy_def(capability_id))

    bridge._canonicalize_production_metadata()

    definitions = bridge.registry.all_definitions()
    assert len(definitions) == 16
    assert {d.name for d in definitions} == EXPECTED_16

    unclassified_side_effect = [d for d in definitions if d.side_effect_class is None]
    blank_sensitivity = [
        d for d in definitions if not str(d.data_sensitivity or "").strip()
    ]
    assert unclassified_side_effect == []
    assert blank_sensitivity == []
    assert len(unclassified_side_effect) == 0
    assert len(blank_sensitivity) == 0

    by_name = {d.name: d for d in definitions}
    assert by_name["file.read"].side_effect_class == SideEffectClass.READ_ONLY
    assert by_name["file.read"].data_sensitivity == "local_user_files"
    assert by_name["market.event.resolve"].side_effect_class == SideEffectClass.READ_ONLY
    assert by_name["market.event.resolve"].data_sensitivity == "market_observe"
    assert by_name["research.event.enrich"].side_effect_class == SideEffectClass.READ_ONLY
    assert by_name["research.event.enrich"].data_sensitivity == "external_research_observation"
    assert by_name["engineering.code_review"].side_effect_class == SideEffectClass.EXTERNAL_SIDE_EFFECT
    assert by_name["engineering.code_review"].data_sensitivity == "engineering_code_review"


def test_full_16_row_mapping_matches_frozen_table():
    bridge = RuntimeCapabilityBridge()
    for capability_id in BASELINE_IDS:
        bridge.registry.register_definition(_legacy_def(capability_id))
    bridge._canonicalize_production_metadata()
    by_name = {d.name: d for d in bridge.registry.all_definitions()}

    for capability_id, metadata in _P3CC_CANONICAL_METADATA.items():
        definition = by_name[capability_id]
        assert definition.side_effect_class == metadata.side_effect_class
        assert definition.data_sensitivity == metadata.data_sensitivity
        assert definition.idempotency_support == metadata.idempotency_support


def test_provider_absent_initialize_path_canonicalizes_and_activates():
    """Real RuntimeCapabilityBridge.initialize() in the provider-absent
    composition (no ai_theme_app provider bound) registers the frozen surface,
    canonicalizes before manager construction, and activates cleanly."""
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    assert bridge._initialized is True
    assert bridge._manager is not None

    definitions = bridge.registry.all_definitions()
    assert len(definitions) == 9  # 3 file.* + 4 frozen market.* + enrich + code_review
    unclassified_side_effect = [
        d for d in definitions if d.side_effect_class is None
    ]
    blank_sensitivity = [
        d for d in definitions if not str(d.data_sensitivity or "").strip()
    ]
    assert unclassified_side_effect == []
    assert blank_sensitivity == []
    assert bridge.manager.registry is bridge.registry  # single registry
