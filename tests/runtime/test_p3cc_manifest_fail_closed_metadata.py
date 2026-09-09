"""P3-CC I1a — fail-closed manifest metadata admission tests.

Proves the C-08 metadata admission law:
  unclassified side_effect ≠ READ_ONLY
  blank data_sensitivity ≠ PUBLIC / safe
  both missing → BOTH exact reasons in deterministic order
  no silent defaulting, no silent single-reason truncation.
"""

from __future__ import annotations

import pytest

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityStatus,
    SideEffectClass,
)
from julia_core.capability.registry import (
    metadata_admission_reasons,
    project_manifest_entry,
)


def _def(**overrides) -> CapabilityDefinition:
    base = dict(
        name="cap.x",
        description="test",
        layer=CapabilityLayer.KNOWLEDGE,
        provider="local",
        permission_scope="file.read",
        input_schema={},
        status=CapabilityStatus.AVAILABLE,
    )
    base.update(overrides)
    return CapabilityDefinition(**base)


@pytest.mark.parametrize(
    "definition, expected_reasons",
    [
        (
            _def(side_effect_class=None, data_sensitivity=""),
            ("unclassified_side_effect", "unclassified_data_sensitivity"),
        ),
        (
            _def(side_effect_class=None, data_sensitivity="local_user_files"),
            ("unclassified_side_effect",),
        ),
        (
            _def(side_effect_class=SideEffectClass.READ_ONLY, data_sensitivity=""),
            ("unclassified_data_sensitivity",),
        ),
    ],
)
def test_unclassified_definitions_are_non_admitted(definition, expected_reasons):
    assert metadata_admission_reasons(definition) == expected_reasons
    admission = project_manifest_entry(definition)
    assert admission.admitted is False
    assert admission.entry is None
    assert admission.reasons == expected_reasons


def test_both_missing_preserves_both_reasons_in_deterministic_order():
    definition = _def(side_effect_class=None, data_sensitivity="")
    reasons = project_manifest_entry(definition).reasons
    assert reasons == (
        "unclassified_side_effect",
        "unclassified_data_sensitivity",
    )
    # Deterministic across calls.
    assert metadata_admission_reasons(definition) == reasons


def test_missing_side_effect_is_never_read_only():
    definition = _def(side_effect_class=None, data_sensitivity="local_user_files")
    admission = project_manifest_entry(definition)
    assert admission.admitted is False
    # A non-admitted definition must never be projected as READ_ONLY.
    assert definition.side_effect_class is None


def test_blank_sensitivity_is_never_public():
    definition = _def(side_effect_class=SideEffectClass.READ_ONLY, data_sensitivity="")
    assert definition.data_sensitivity == ""
    admission = project_manifest_entry(definition)
    assert admission.admitted is False
    assert "unclassified_data_sensitivity" in admission.reasons


def test_explicit_side_effect_and_sensitivity_are_admitted():
    definition = _def(
        side_effect_class=SideEffectClass.READ_ONLY,
        data_sensitivity="local_user_files",
    )
    assert metadata_admission_reasons(definition) == ()
    admission = project_manifest_entry(definition)
    assert admission.admitted is True
    assert admission.entry is not None
    assert admission.entry.side_effect_class == SideEffectClass.READ_ONLY
    assert admission.entry.data_sensitivity == "local_user_files"
