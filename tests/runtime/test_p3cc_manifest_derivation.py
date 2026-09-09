"""P3-CC I1a-R2 — CapabilityManifestEntry derivation seam tests.

Proves the manifest projection is a derived, model-visible C-08 projection
that (a) uses canonical capability_id, (b) isolates mutable metadata, (c)
derives permission requirements from the single frozen source
``CapabilityDefinition.permission_scope`` with NO caller override, (d) accepts
availability ONLY as an explicitly derived required input (never from
administrative status), (e) carries a concrete non-optional SideEffectClass,
(f) includes provenance ``derived_at``, and (g) refuses to yield an executable
entry for an unclassified definition.
"""

from __future__ import annotations

import dataclasses
import typing

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
    admission = project_manifest_entry(
        definition, availability=CapabilityStatus.AVAILABLE
    )
    assert admission.admitted is True
    assert admission.reasons == ()
    assert admission.entry is not None
    assert isinstance(admission.entry, CapabilityManifestEntry)
    assert admission.entry.capability_id == "file.read"
    assert admission.entry.schema_version == "1.0"


def test_manifest_side_effect_type_is_concrete_not_optional():
    """CapabilityManifestEntry.side_effect_class is non-optional
    SideEffectClass; CapabilityDefinition keeps the None sentinel."""
    definition = _explicit_def("file.read")
    assert definition.side_effect_class == SideEffectClass.READ_ONLY

    hints = typing.get_type_hints(CapabilityManifestEntry)
    # Manifest field is the concrete enum, not an Optional union.
    assert hints["side_effect_class"] == SideEffectClass
    assert not typing.get_args(hints["side_effect_class"])

    definition_hints = typing.get_type_hints(CapabilityDefinition)
    definition_args = typing.get_args(definition_hints["side_effect_class"])
    assert SideEffectClass in definition_args
    assert type(None) in definition_args  # None sentinel preserved

    admission = project_manifest_entry(
        definition, availability=CapabilityStatus.AVAILABLE
    )
    assert admission.entry is not None
    assert admission.entry.side_effect_class == SideEffectClass.READ_ONLY
    # An admitted executable manifest never carries an unclassified sentinel.
    assert admission.entry.side_effect_class is not None


def test_manifest_copies_and_isolates_mutable_metadata():
    definition = _explicit_def("file.read")
    admission = project_manifest_entry(
        definition, availability=CapabilityStatus.AVAILABLE
    )
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


def test_permission_requirements_have_single_frozen_source():
    """Manifest permission requirements == (definition.permission_scope,); no
    projection parameter exists that can override it."""
    definition = _explicit_def("market.event.resolve", scope="market.observe")
    admission = project_manifest_entry(
        definition, availability=CapabilityStatus.AVAILABLE
    )
    assert admission.entry is not None
    assert admission.entry.permission_requirements == ("market.observe",)

    # No override parameter is accepted by the projection API.
    import inspect

    signature = inspect.signature(project_manifest_entry)
    assert "permission_requirements" not in signature.parameters


def test_no_provider_or_adapter_field_is_semantic_selection_authority():
    definition = _explicit_def("file.read", scope="file.read")
    admission = project_manifest_entry(
        definition, availability=CapabilityStatus.AVAILABLE
    )
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
    admission = project_manifest_entry(
        definition, availability=CapabilityStatus.AVAILABLE
    )
    assert admission.admitted is False
    assert admission.entry is None
    assert admission.reasons == (
        "unclassified_side_effect",
        "unclassified_data_sensitivity",
    )
    # metadata_admission_reasons agrees (deterministic, all reasons).
    assert metadata_admission_reasons(definition) == admission.reasons


def test_availability_is_required_external_input_and_not_overwritten():
    """Registry never derives availability from administrative status.

    definition.status = AVAILABLE but the caller-supplied derived availability
    is REGISTERED → manifest.availability MUST be REGISTERED (the registry
    honors the CapabilityFrame-derived value and never substitutes status).
    """
    definition = _explicit_def("file.read")  # status = AVAILABLE
    admission = project_manifest_entry(
        definition, availability=CapabilityStatus.REGISTERED
    )
    assert admission.entry is not None
    assert admission.entry.availability == CapabilityStatus.REGISTERED

    # Omitting availability is not accepted by the API.
    with pytest.raises(TypeError):
        project_manifest_entry(definition)  # type: ignore[call-arg]


def test_manifest_provenance_has_source_ref_and_derived_at():
    definition = _explicit_def("file.read")
    admission = project_manifest_entry(
        definition, availability=CapabilityStatus.AVAILABLE
    )
    assert admission.entry is not None
    provenance = admission.entry.provenance
    assert provenance["source"] == "capability:registry"
    assert provenance["definition_ref"] == "file.read"
    assert "derived_at" in provenance
    derived_at = provenance["derived_at"]
    assert isinstance(derived_at, str)
    assert derived_at.strip() != ""
    # ISO 8601-ish shape: YYYY-MM-DDTHH:MM:SSZ
    assert derived_at[4] == "-" and derived_at[7] == "-"
    assert derived_at[-1] == "Z"
    # No provider or semantic-routing material in provenance.
    assert "provider" not in provenance
    assert "router" not in provenance
    assert "intent" not in provenance
