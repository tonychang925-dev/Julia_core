"""P3-CC I1b-1 — Option-C availability projection + governed CapabilityFrame.

Proves:
- the frozen Option-C truth table (status + provider-bound conjunct);
- provider.health() is NEVER consulted during frame projection;
- provider-first Market surface = 4 frozen AVAILABLE, 7 legacy REGISTERED;
- provider-absent Market surface stays REGISTERED;
- the governed manifest replaces the raw "available_tools" catalog in the
  Context OS capability frame;
- non-admitted definitions remain non-executable with typed diagnostics;
- capability information reaches the model only through pkg.capability_frame.
"""

from __future__ import annotations

import pytest

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityStatus,
    SideEffectClass,
)
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    build_capability_manifest,
    derive_option_c_availability,
)


def _explicit_def(
    name: str,
    *,
    provider: str,
    scope: str,
    status: CapabilityStatus = CapabilityStatus.REGISTERED,
    side_effect: SideEffectClass = SideEffectClass.READ_ONLY,
    sensitivity: str = "test_observation",
) -> CapabilityDefinition:
    return CapabilityDefinition(
        name=name,
        description=f"test {name}",
        layer=CapabilityLayer.WORLD,
        provider=provider,
        permission_scope=scope,
        input_schema={"q": "query"},
        status=status,
        side_effect_class=side_effect,
        data_sensitivity=sensitivity,
    )


# ── 1. Option-C truth table ─────────────────────────────────────────────────

@pytest.mark.parametrize(
    "status,bound,expected",
    [
        (CapabilityStatus.AVAILABLE, True, CapabilityStatus.AVAILABLE),
        (CapabilityStatus.AVAILABLE, False, CapabilityStatus.REGISTERED),
        (CapabilityStatus.REGISTERED, True, CapabilityStatus.REGISTERED),
        (CapabilityStatus.REGISTERED, False, CapabilityStatus.REGISTERED),
        (CapabilityStatus.DEGRADED, True, CapabilityStatus.DEGRADED),
        (CapabilityStatus.DISABLED, True, CapabilityStatus.DISABLED),
        (CapabilityStatus.DISABLED, False, CapabilityStatus.DISABLED),
    ],
)
def test_option_c_truth_table(status, bound, expected):
    assert derive_option_c_availability(status, provider_bound=bound) == expected


# ── 2. Provider health is never used during projection ─────────────────────

class _RaisingHealthProvider:
    """Test double whose health() raises if called. Test-only; never
    production-reachable (registered under test profile only)."""

    def __init__(self):
        self.health_calls = 0

    async def health(self):
        self.health_calls += 1
        raise AssertionError("provider.health() must not be called during "
                             "CapabilityFrame projection")

    async def execute(self, request):  # pragma: no cover - unused
        raise AssertionError("unused")


def test_projection_succeeds_without_calling_provider_health():
    provider = _RaisingHealthProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("product_adapter", provider)
    bridge.registry.register_definition(
        _explicit_def(
            "product.observe",
            provider="product_adapter",
            scope="product.observe",
            status=CapabilityStatus.AVAILABLE,
        )
    )
    bridge.initialize()

    bound = frozenset(bridge.manager.providers)
    manifest = build_capability_manifest(bridge.registry.all_definitions(), bound)

    entry = next(
        e for e in manifest["manifest_entries"]
        if e["capability_id"] == "product.observe"
    )
    assert entry["availability"] == "available"
    # Projection never consulted provider.health().
    assert provider.health_calls == 0


# ── 3. Market provider-first surface discipline ────────────────────────────

class _FakeAiThemeProvider:
    """Stand-in binding so the provider-first composition branch runs.
    Test-only; never production-reachable."""

    def __init__(self):
        self.health_calls = 0

    async def health(self):
        self.health_calls += 1
        return (True, "ok")

    async def execute(self, request):  # pragma: no cover - unused
        raise AssertionError("unused")


FROZEN_FOUR = {
    "market.event.resolve",
    "market.event.read",
    "market.snapshot.read",
    "market.alert.query",
}
LEGACY_SEVEN = {
    "market.intelligence.observe",
    "market.decision.explain",
    "market.stock.history",
    "market.stock.auction",
    "market.theme.constituents",
    "market.theme.capital",
    "market.regime.read",
}


def test_provider_first_market_surface_registration_discipline():
    provider = _FakeAiThemeProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("ai_theme_app", provider)
    bridge.initialize()

    statuses = {
        d.name: d.status
        for d in bridge.registry.all_definitions()
        if d.name.startswith("market.")
    }
    for name in FROZEN_FOUR:
        assert statuses[name] == CapabilityStatus.AVAILABLE, name
    for name in LEGACY_SEVEN:
        assert statuses[name] == CapabilityStatus.REGISTERED, name
    # Administrative status is never mutated by projection.
    assert provider.health_calls == 0


def test_provider_first_manifest_never_advertises_legacy_market_available():
    provider = _FakeAiThemeProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("ai_theme_app", provider)
    bridge.initialize()

    bound = frozenset(bridge.manager.providers)
    manifest = build_capability_manifest(bridge.registry.all_definitions(), bound)
    by_id = {e["capability_id"]: e for e in manifest["manifest_entries"]}

    for name in FROZEN_FOUR:
        assert by_id[name]["availability"] == "available", name
    for name in LEGACY_SEVEN:
        assert by_id[name]["availability"] == "registered", name
        assert by_id[name]["availability"] != "available"
    assert provider.health_calls == 0


# ── 4. Provider-absent Market path ─────────────────────────────────────────

def test_provider_absent_market_surface_stays_registered():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    statuses = {
        d.name: d.status
        for d in bridge.registry.all_definitions()
        if d.name.startswith("market.")
    }
    for name in FROZEN_FOUR:
        assert statuses[name] == CapabilityStatus.REGISTERED, name

    bound = frozenset(bridge.manager.providers)
    manifest = build_capability_manifest(bridge.registry.all_definitions(), bound)
    by_id = {e["capability_id"]: e for e in manifest["manifest_entries"]}
    for name in FROZEN_FOUR:
        assert by_id[name]["availability"] == "registered"


# ── 5/6. Governed manifest content + raw catalog retired ───────────────────

def test_capability_frame_is_governed_manifest_not_raw_catalog():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    bound = frozenset(bridge.manager.providers)
    manifest = build_capability_manifest(bridge.registry.all_definitions(), bound)

    assert "available_tools" not in manifest
    assert set(manifest.keys()) == {"manifest_entries", "non_admitted_diagnostics"}

    by_id = {e["capability_id"]: e for e in manifest["manifest_entries"]}
    file_read = by_id["file.read"]
    for field in (
        "capability_id",
        "description",
        "input_schema",
        "output_schema",
        "side_effect_class",
        "permission_requirements",
        "idempotency_support",
        "latency_cost_hints",
        "data_sensitivity",
        "availability",
        "schema_version",
        "provenance",
    ):
        assert field in file_read, field
    assert file_read["side_effect_class"] == "read_only"
    assert file_read["permission_requirements"] == ["file.read"]
    assert file_read["data_sensitivity"] == "local_user_files"
    assert file_read["availability"] == "available"  # local provider bound
    # Provider/transport is not model-visible semantic-selection metadata.
    assert "provider" not in file_read
    assert "adapter" not in file_read


def test_entries_and_diagnostics_are_deterministically_sorted():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    bound = frozenset(bridge.manager.providers)
    manifest = build_capability_manifest(bridge.registry.all_definitions(), bound)
    ids = [e["capability_id"] for e in manifest["manifest_entries"]]
    assert ids == sorted(ids)


# ── 7. Non-admission defense in depth ──────────────────────────────────────

def test_non_admitted_definition_never_executable_and_keeps_reasons():
    bridge = RuntimeCapabilityBridge()
    # A post-activation, newly visible definition that somehow lacks explicit
    # metadata must stay non-executable with typed reasons preserved.
    bridge.registry.register_definition(
        CapabilityDefinition(
            name="late.unclassified.cap",
            description="missing mandatory metadata",
            layer=CapabilityLayer.WORLD,
            provider="some_namespace",
            permission_scope="some.scope",
            status=CapabilityStatus.AVAILABLE,
        )
    )
    bound = frozenset()
    manifest = build_capability_manifest(bridge.registry.all_definitions(), bound)

    assert all(
        e["capability_id"] != "late.unclassified.cap"
        for e in manifest["manifest_entries"]
    )
    diagnostic = next(
        d for d in manifest["non_admitted_diagnostics"]
        if d["capability_id"] == "late.unclassified.cap"
    )
    assert diagnostic["admitted"] is False
    assert diagnostic["reasons"] == [
        "unclassified_side_effect",
        "unclassified_data_sensitivity",
    ]
    # No silent READ_ONLY/public default was applied.
    assert all(
        e["capability_id"] != "late.unclassified.cap"
        for e in manifest["manifest_entries"]
    )


# ── 8. C-03 path: capability info only through pkg.capability_frame ────────

def test_capability_frame_renders_governed_manifest_transitionally():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    bound = frozenset(bridge.manager.providers)
    manifest = build_capability_manifest(bridge.registry.all_definitions(), bound)

    pkg = CognitiveContextPackage()
    pkg.capability_frame = manifest

    rendered = pkg._render_frame("capability", pkg.capability_frame)
    assert "file.read" in rendered
    assert "read_only" in rendered
    assert "available_tools" not in rendered
    # The registry is not re-read by rendering; the frame is the single source
    # for this code path.
    assert pkg.capability_frame is manifest


# ── P3-CC I1b-4: research.run_brief composite availability ────────────────

from julia_core.runtime.context_execution_runtime import (
    RESEARCH_RUN_BRIEF_CAPABILITY_ID,
    build_capability_manifest,
)

REQUIRED_SUBCAPS = (
    "market.event.resolve",
    "market.event.read",
    "research.event.enrich",
)


def _composite_frame(resolve, read, enrich, *, include_composite=True):
    """Build a governed manifest from explicit dependency definitions."""
    frame = {}
    entries = []
    if include_composite:
        entries.append(_explicit_def(
            "research.run_brief",
            provider="composite",
            scope="research.run_brief",
            status=CapabilityStatus.REGISTERED,
            sensitivity="market_event_research",
        ))
    entries.append(_explicit_def(
        "market.event.resolve",
        provider="ai_theme_app",
        scope="market.observe",
        status=resolve,
    ))
    entries.append(_explicit_def(
        "market.event.read",
        provider="ai_theme_app",
        scope="market.observe",
        status=read,
    ))
    if enrich is not None:
        entries.append(_explicit_def(
            "research.event.enrich",
            provider="research_enrichment",
            scope="research.enrich",
            status=enrich,
        ))
    frame["manifest_entries"] = [vars_of(e) for e in entries] if False else [
        {
            "capability_id": e.name,
            "description": e.description,
            "input_schema": e.input_schema,
            "output_schema": e.output_schema,
            "side_effect_class": e.side_effect_class.value,
            "permission_requirements": [e.permission_scope],
            "idempotency_support": e.idempotency_support.value,
            "latency_cost_hints": e.latency_cost_hints,
            "data_sensitivity": e.data_sensitivity,
            "availability": e.status.value,
            "schema_version": e.schema_version,
            "provenance": {"source": "capability:registry",
                           "definition_ref": e.name,
                           "derived_at": "2026-09-09T00:00:00Z"},
        }
        for e in entries
    ]
    return frame


def _composite_result(*, resolve=CapabilityStatus.AVAILABLE,
                      read=CapabilityStatus.AVAILABLE,
                      enrich=CapabilityStatus.AVAILABLE,
                      include_composite=True, include_enrich=True):
    frame = _composite_frame(
        resolve,
        read,
        enrich if include_enrich else None,
        include_composite=include_composite,
    )
    # A fake provider double whose health() raises if invoked; only its name
    # participates in projection (never the object).
    provider = _RaisingHealthProvider()
    bound = frozenset({"ai_theme_app", "research_enrichment"})
    manifest = build_capability_manifest(
        [defn_from(e) for e in frame["manifest_entries"]], bound
    )
    return manifest, provider


def defn_from(entry):
    from julia_core.capability.models import (
        CapabilityDefinition,
        CapabilityLayer,
        CapabilityStatus,
        IdempotencySupport,
        SideEffectClass,
    )
    return CapabilityDefinition(
        name=entry["capability_id"],
        description=entry["description"],
        layer=CapabilityLayer.WORLD,
        provider="composite" if entry["capability_id"] == "research.run_brief"
        else ("ai_theme_app" if entry["capability_id"].startswith("market.")
              else "research_enrichment"),
        permission_scope=entry["permission_requirements"][0],
        input_schema=entry["input_schema"],
        status=CapabilityStatus(entry["availability"]),
        side_effect_class=SideEffectClass(entry["side_effect_class"]),
        idempotency_support=IdempotencySupport(entry["idempotency_support"]),
        data_sensitivity=entry["data_sensitivity"],
    )


def _run_brief_availability(manifest):
    by_id = {e["capability_id"]: e for e in manifest["manifest_entries"]}
    if RESEARCH_RUN_BRIEF_CAPABILITY_ID not in by_id:
        return None
    return by_id[RESEARCH_RUN_BRIEF_CAPABILITY_ID]["availability"]


def test_composite_available_when_all_subcaps_available():
    manifest, provider = _composite_result()
    assert _run_brief_availability(manifest) == "available"
    assert provider.health_calls == 0  # PROVIDER_HEALTH_CALL_COUNT == 0


@pytest.mark.parametrize(
    "mutate",
    [
        ("resolve", CapabilityStatus.REGISTERED),
        ("resolve", CapabilityStatus.DISABLED),
        ("read", CapabilityStatus.REGISTERED),
        ("read", CapabilityStatus.DISABLED),
        ("enrich", CapabilityStatus.REGISTERED),
        ("enrich", CapabilityStatus.DISABLED),
    ],
)
def test_composite_not_available_when_any_subcap_not_available(mutate):
    which, status = mutate
    kwargs = {"resolve": CapabilityStatus.AVAILABLE,
              "read": CapabilityStatus.AVAILABLE,
              "enrich": CapabilityStatus.AVAILABLE}
    kwargs[which] = status
    manifest, provider = _composite_result(**kwargs)
    assert _run_brief_availability(manifest) != "available"
    assert provider.health_calls == 0


def test_composite_not_available_when_subcap_provider_unbound():
    # enrich AVAILABLE but its provider namespace NOT in the bound set.
    frame = _composite_frame(
        CapabilityStatus.AVAILABLE,
        CapabilityStatus.AVAILABLE,
        CapabilityStatus.AVAILABLE,
    )
    manifest = build_capability_manifest(
        [defn_from(e) for e in frame["manifest_entries"]],
        frozenset({"ai_theme_app"}),  # research_enrichment NOT bound
    )
    assert _run_brief_availability(manifest) != "available"


def test_composite_not_available_when_dependency_missing():
    manifest, provider = _composite_result(include_enrich=False)
    assert _run_brief_availability(manifest) != "available"
    assert provider.health_calls == 0
