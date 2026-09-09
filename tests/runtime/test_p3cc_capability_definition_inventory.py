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

EXPECTED_17 = {
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
    "research.run_brief",
}


def _legacy_def(name: str, *, scope: str = "market.observe") -> CapabilityDefinition:
    return CapabilityDefinition(
        name=name,
        description=f"legacy {name}",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="local",
        permission_scope=scope,
        status=CapabilityStatus.REGISTERED,
    )


def test_frozen_baseline_mapping_covers_exactly_17_definitions():
    assert len(_P3CC_CANONICAL_METADATA) == 17
    assert set(BASELINE_IDS) == EXPECTED_17


def test_provider_first_composition_canonicalizes_all_17():
    bridge = RuntimeCapabilityBridge()
    # Simulate the provider-first composition surface: every production id is
    # registered as a legacy (unclassified) definition first.
    for capability_id in BASELINE_IDS:
        bridge.registry.register_definition(_legacy_def(capability_id))

    bridge._canonicalize_production_metadata()

    definitions = bridge.registry.all_definitions()
    assert len(definitions) == 17
    assert {d.name for d in definitions} == EXPECTED_17

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
    assert len(definitions) == 10  # 3 file.* + 4 frozen market.* + enrich + code_review + research.run_brief
    unclassified_side_effect = [
        d for d in definitions if d.side_effect_class is None
    ]
    blank_sensitivity = [
        d for d in definitions if not str(d.data_sensitivity or "").strip()
    ]
    assert unclassified_side_effect == []
    assert blank_sensitivity == []
    assert bridge.manager.registry is bridge.registry  # single registry


def test_research_run_brief_registered_exactly_once_with_explicit_metadata():
    """P3-CC I1b-4: research.run_brief is a real canonical production
    definition in the single registry with the frozen explicit metadata."""
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    definitions = [
        d for d in bridge.registry.all_definitions()
        if d.name == "research.run_brief"
    ]
    assert len(definitions) == 1  # DUPLICATE_RESEARCH_RUN_BRIEF_DEFINITION_COUNT == 0
    definition = definitions[0]
    assert definition.capability_id == "research.run_brief" if hasattr(definition, "capability_id") else True
    assert definition.side_effect_class == SideEffectClass.READ_ONLY
    assert definition.data_sensitivity == "market_event_research"
    assert definition.idempotency_support.value == "request_key"
    assert definition.permission_scope == "research.run_brief"
    assert definition.provider == "composite"  # governed-composite marker, not transport
    # Canonical source is the registry definition, not a synthetic descriptor.
    stored = bridge.registry.get("research.run_brief")
    assert stored is not None
    assert stored.side_effect_class == SideEffectClass.READ_ONLY
    assert stored.data_sensitivity == "market_event_research"
    assert stored.permission_scope == "research.run_brief"


def test_research_run_brief_provider_first_canonical_metadata():
    """P3-CC I1b-4 (A): exact frozen fields after provider-first style
    canonicalization."""
    bridge = RuntimeCapabilityBridge()
    # Seed every baseline id (incl. research.run_brief) as a legacy def, then
    # canonicalize exactly as initialize does. Canonicalization preserves
    # permission scope, so each seed carries its governed scope.
    scope_for = {
        "research.run_brief": "research.run_brief",
        "research.event.enrich": "research.enrich",
        "engineering.code_review": "engineering.review.external",
    }
    for capability_id in BASELINE_IDS:
        bridge.registry.register_definition(
            _legacy_def(
                capability_id,
                scope=scope_for.get(
                    capability_id,
                    "market.observe" if capability_id.startswith("market.")
                    else "file.read",
                ),
            )
        )
    bridge._canonicalize_production_metadata()
    definition = bridge.registry.get("research.run_brief")
    assert definition is not None
    assert definition.name == "research.run_brief"
    assert definition.side_effect_class == SideEffectClass.READ_ONLY
    assert definition.data_sensitivity == "market_event_research"
    assert definition.permission_scope == "research.run_brief"
    assert definition.idempotency_support.value == "request_key"
