"""P3-CC I1a — CapabilityManifestEntry derivation seam tests.

Proves the manifest projection is a derived, model-visible C-08 projection
that (a) uses canonical capability_id, (b) isolates mutable metadata, (c)
derives permission requirements from governed definition semantics, (d) never
exposes provider/transport as semantic-selection authority, and (e) refuses to
yield an executable entry for an unclassified definition.
"""

from __future__ import annotations

import dataclasses

import pytest

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityManifestEntry,
    CapabilityStatus,
    SideEffectClass,
)
from julia_core.capability.registry import (
    CapabilityRegistry,
    metadata_admission_reasons,
    project_manifest_entry,
)


def _legacy_def(name: str, *, scope: str = "file.read") -> CapabilityDefinition:
    """A legacy-compatible definition with NO P3-CC metadata."""
    return CapabilityDefinition(
        name=name,
        description=f"test capability {name}",
        layer=CapabilityLayer.KNOWLEDGE,
        provider="local",
        permission_scope=scope,
        input_schema={"path": "file path"},
        adapter=None,
        status=CapabilityStatus.AVAILABLE,
        schema_version="1.0",
    )


def _explicit_def(name: str, *, scope: str = "file.read") -> CapabilityDefinition:
    return CapabilityDefinition(
        name=name,
        description=f"test capability {name}",
        layer=CapabilityLayer.KNOWLEDGE,
        provider="local",
        permission_scope=scope,
        input_schema={"path": "file path"},
        adapter=None,
        status=CapabilityStatus.AVAILABLE,
        schema_version="1.0",
        output_schema={"content": "decoded file text"},
        side_effect_class=SideEffectClass.READ_ONLY,
        idempotency_support="request_key",
        latency_cost_hints={"class": "file_read"},
        data_sensitivity="local_user_files",
    )


def test_new_metadata_survives_registration():
    registry = CapabilityRegistry()
    definition = _explicit_def("file.read")
    registry.register_definition(definition)
    stored = registry.get("file.read")
    assert stored is not None
    assert stored.side_effect_class == SideEffectClass.READ_ONLY
    assert stored.data_sensitivity == "local_user_files"
    assert stored.output_schema == {"content": "decoded file text"}
    assert stored.latency_cost_hints == {"class": "file_read"}


def test_manifest_entry_uses_canonical_capability_id():
    definition = _explicit_def("file.read")
    admission = project_manifest_entry(definition)
    assert admission.admitted is True
    assert admission.reasons == ()
    assert admission.entry is not None
    assert isinstance(admission.entry, CapabilityManifestEntry)
    assert admission.entry.capability_id == "file.read"
    assert admission.entry.schema_version == "1.0"


def test_manifest_copies_and_isolates_mutable_metadata():
    definition = _explicit_def("file.read")
    admission = project_manifest_entry(definition)
    assert admission.entry is not None
    assert admission.entry.input_schema is not definition.input_schema
    assert admission.entry.output_schema is not definition.output_schema
    assert admission.entry.latency_cost_hints is not definition.latency_cost_hints

    # Mutating the source definition's mutable dicts after projection must not
    # leak into the already-derived entry.
    definition.input_schema["injected"] = "leak"
    definition.latency_cost_hints["injected"] = "leak"
    assert "injected" not in admission.entry.input_schema
    assert "injected" not in admission.entry.latency_cost_hints


def test_permission_requirement_derives_from_governed_scope():
    definition = _explicit_def("market.event.resolve", scope="market.observe")
    admission = project_manifest_entry(definition)
    assert admission.entry is not None
    assert admission.entry.permission_requirements == ("market.observe",)

    explicit = project_manifest_entry(
        definition, permission_requirements=("market.observe", "research.observe")
    )
    assert explicit.entry is not None
    assert explicit.entry.permission_requirements == (
        "market.observe",
        "research.observe",
    )


def test_no_provider_or_adapter_field_is_semantic_selection_authority():
    definition = _explicit_def("file.read", scope="file.read")
    admission = project_manifest_entry(definition)
    assert admission.entry is not None
    fields = {f.name for f in dataclasses.fields(CapabilityManifestEntry)}
    # Provider/transport/execution fields must not be model-owned selection
    # authority in the manifest projection.
    assert "provider" not in fields
    assert "adapter" not in fields
    assert "endpoint" not in fields
    assert "router" not in fields
    assert "intent" not in fields
    assert "model_invocable" not in fields
    assert "transport" not in fields


def test_unclassified_definition_cannot_yield_executable_manifest():
    definition = _legacy_def("file.search")
    admission = project_manifest_entry(definition)
    assert admission.admitted is False
    assert admission.entry is None
    assert admission.reasons == (
        "unclassified_side_effect",
        "unclassified_data_sensitivity",
    )
    # metadata_admission_reasons agrees (deterministic, all reasons).
    assert metadata_admission_reasons(definition) == admission.reasons


def test_availability_defaults_to_administrative_status_conservatively():
    definition = _explicit_def("file.read")
    definition = CapabilityDefinition(
        name=definition.name,
        description=definition.description,
        layer=definition.layer,
        provider=definition.provider,
        permission_scope=definition.permission_scope,
        input_schema=definition.input_schema,
        adapter=definition.adapter,
        status=CapabilityStatus.REGISTERED,
        schema_version=definition.schema_version,
        output_schema=definition.output_schema,
        side_effect_class=definition.side_effect_class,
        idempotency_support=definition.idempotency_support,
        latency_cost_hints=definition.latency_cost_hints,
        data_sensitivity=definition.data_sensitivity,
    )
    admission = project_manifest_entry(definition)
    assert admission.entry is not None
    # Option C conservative base: administrative status, no live projection.
    assert admission.entry.availability == CapabilityStatus.REGISTERED
