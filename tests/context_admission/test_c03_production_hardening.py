from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

import pytest

from julia_core.identity import IdentityStatus
from julia_core.memory_experience import MemoryExperienceStatus
from julia_core.projection.contracts import ExperienceFrameSet

from julia_core.context_admission import (
    AdmissionRejection,
    C03AdmissionRejected,
    CanonicalConversationProvenance,
    CanonicalConversationSource,
    CurrentConversationalTaskContext,
    ExclusiveAdmissionGate,
    ExclusiveAdmissionRequest,
    ModelVisibilityTransport,
)
from julia_core.context_admission.gate import C03_PRODUCTION_CONTRACT_VERSION

from .production_fixtures import (
    canonical_current_task_context,
    canonical_experience_frame,
    canonical_experience_frame_set,
    canonical_identity_frame,
    canonical_request,
)


@pytest.mark.parametrize(
    "status",
    [
        IdentityStatus.CANDIDATE,
        IdentityStatus.SUPERSEDED,
        IdentityStatus.RETIRED,
    ],
)
def test_only_exact_admitted_identity_status_can_enter(status: IdentityStatus) -> None:
    request = canonical_request(
        identity=replace(canonical_identity_frame(), source_status=status)
    )

    with pytest.raises(C03AdmissionRejected) as error:
        ExclusiveAdmissionGate().seal(request)

    assert error.value.rejection.code == "non_admitted_source"
    assert error.value.rejection.to_dict()["partial_admission"] is False


@pytest.mark.parametrize(
    "status",
    [
        MemoryExperienceStatus.CANDIDATE,
        MemoryExperienceStatus.SUPERSEDED,
        MemoryExperienceStatus.RETIRED,
    ],
)
def test_only_exact_admitted_experience_status_can_enter(
    status: MemoryExperienceStatus,
) -> None:
    request = canonical_request(
        experiences=ExperienceFrameSet(
            schema_version="1.0.0",
            frames=(replace(canonical_experience_frame(), source_status=status),),
        )
    )

    with pytest.raises(C03AdmissionRejected) as error:
        ExclusiveAdmissionGate().seal(request)

    assert error.value.rejection.code == "non_admitted_source"


def test_frame_provenance_must_bind_exact_source_digest() -> None:
    identity = canonical_identity_frame(
        provenance_refs=({"source_ref": "fixture://wrong", "source_digest": "d" * 64},)
    )
    experience = canonical_experience_frame(
        provenance_refs=({"source_ref": "fixture://wrong", "source_digest": "e" * 64},)
    )
    experiences = ExperienceFrameSet(
        schema_version="1.0.0", frames=(experience,)
    )

    with pytest.raises(C03AdmissionRejected, match="identity frame provenance digest"):
        ExclusiveAdmissionGate().seal(canonical_request(identity=identity))
    with pytest.raises(C03AdmissionRejected, match="experience frame provenance digest"):
        ExclusiveAdmissionGate().seal(canonical_request(experiences=experiences))


@pytest.mark.parametrize("field_name", ["policy_id", "policy_version", "schema_version"])
def test_non_canonical_projection_contracts_fail_closed(field_name: str) -> None:
    identity = replace(canonical_identity_frame(), **{field_name: "forged"})
    experience = replace(canonical_experience_frame(), **{field_name: "forged"})
    experiences = ExperienceFrameSet(schema_version="1.0.0", frames=(experience,))

    with pytest.raises(C03AdmissionRejected, match="identity frame projection contract"):
        ExclusiveAdmissionGate().seal(canonical_request(identity=identity))
    with pytest.raises(C03AdmissionRejected, match="experience frame projection contract"):
        ExclusiveAdmissionGate().seal(canonical_request(experiences=experiences))


def test_forged_package_and_receipt_are_rejected() -> None:
    sealed = ExclusiveAdmissionGate().seal(canonical_request())
    forged = object.__new__(type(sealed))
    for name in type(sealed).__dataclass_fields__:
        object.__setattr__(forged, name, getattr(sealed, name))
    object.__setattr__(forged, "gate_receipt", "0" * 64)

    with pytest.raises(C03AdmissionRejected, match="receipt is forged"):
        ModelVisibilityTransport().render(forged)
    with pytest.raises(C03AdmissionRejected, match="receipt does not match"):
        forged.verify()


def test_forged_package_manifest_is_rejected() -> None:
    sealed = ExclusiveAdmissionGate().seal(canonical_request())
    forged = object.__new__(type(sealed))
    for name in type(sealed).__dataclass_fields__:
        object.__setattr__(forged, name, getattr(sealed, name))
    object.__setattr__(
        forged, "admitted_frames", {"identity_frame": "0" * 64}
    )

    with pytest.raises(C03AdmissionRejected, match="admitted-frame manifest"):
        forged.verify()


def test_semantic_content_change_changes_package_identity() -> None:
    original_identity = canonical_identity_frame()
    changed_identity = replace(
        original_identity,
        anchors=(
            {
                "anchor_id": "boundary",
                "statement": "Use governed context only after review",
            },
        ),
    )
    original_experience = canonical_experience_frame()
    changed_experience = replace(
        original_experience,
        content={"commitment": "Changed governed context admission commitment"},
    )
    changed_experiences = ExperienceFrameSet(
        schema_version="1.0.0", frames=(changed_experience,)
    )

    baseline = ExclusiveAdmissionGate().seal(canonical_request())
    changed_identity_package = ExclusiveAdmissionGate().seal(
        canonical_request(identity=changed_identity)
    )
    changed_experience_package = ExclusiveAdmissionGate().seal(
        canonical_request(experiences=changed_experiences)
    )

    assert changed_identity.digest() != original_identity.digest()
    assert changed_experience.digest() != original_experience.digest()
    assert changed_identity_package.gate_receipt != baseline.gate_receipt
    assert changed_experience_package.gate_receipt != baseline.gate_receipt


def test_package_serialization_is_deterministic_and_detached() -> None:
    first = ExclusiveAdmissionGate().seal(canonical_request())
    second = ExclusiveAdmissionGate().seal(canonical_request())
    outward = first.to_dict()
    outward["authority"]["runtime"] = True
    outward["admitted_frames"]["identity_frame"] = "changed"

    assert first.to_dict() == second.to_dict()
    assert json.dumps(first.to_dict(), sort_keys=True) == json.dumps(
        second.to_dict(), sort_keys=True
    )
    assert first.to_dict()["authority"]["runtime"] is False
    assert first.verify() is first


def test_admitted_package_cannot_mint_downstream_authority() -> None:
    sealed = ExclusiveAdmissionGate().seal(canonical_request())

    assert not hasattr(sealed, "runtime_authority")
    assert not hasattr(sealed, "provider_authority")
    assert not hasattr(sealed, "assistant_authority")
    assert not hasattr(sealed, "canonical_write_authority")
    assert sealed.to_dict()["authority"] == {
        "canonical": False,
        "runtime": False,
        "provider": False,
        "assistant_self": False,
    }


def test_current_task_state_requires_deterministic_json_shape() -> None:
    with pytest.raises(C03AdmissionRejected, match="keys must be exact strings"):
        canonical_current_task_context(bounded_state={1: "invalid"})
    with pytest.raises(C03AdmissionRejected, match="unsupported value"):
        canonical_current_task_context(bounded_state={"value": object()})
    with pytest.raises(C03AdmissionRejected, match="deterministically serializable"):
        canonical_current_task_context(
            bounded_state={"value": float("nan")}
        )


def test_runtime_provenance_source_ref_must_be_exact() -> None:
    def provenance(source_ref: str) -> CanonicalConversationProvenance:
        return CanonicalConversationProvenance(
            source_type=CanonicalConversationSource.CONVERSATION_RUNTIME,
            source_ref=source_ref,
            source_digest="c" * 64,
            observed_at="2026-09-12T00:00:00Z",
        )

    for source_ref in (
        "assistant://current-task",
        "conversation_runtime://",
        "conversation_runtime://agent",
        "conversation_runtime://agent/task?side_channel=1",
        "conversation_runtime://agent/task#fragment",
    ):
        with pytest.raises(C03AdmissionRejected, match="source ref is inexact"):
            canonical_current_task_context(provenance=provenance(source_ref))


def test_request_and_gate_subclasses_cannot_become_admission_authority() -> None:
    class RequestSubclass(ExclusiveAdmissionRequest):
        pass

    class GateSubclass(ExclusiveAdmissionGate):
        pass

    request = RequestSubclass(
        canonical_identity_frame(),
        canonical_experience_frame_set(),
        canonical_current_task_context(),
    )

    with pytest.raises(C03AdmissionRejected, match="request type is inexact"):
        ExclusiveAdmissionGate().seal(request)
    with pytest.raises(C03AdmissionRejected, match="gate type is inexact"):
        GateSubclass().seal(canonical_request())


def test_machine_readable_rejection_is_fail_closed() -> None:
    rejection = AdmissionRejection(
        code="test_rejection", message="exact precondition unavailable"
    )

    assert rejection.to_dict() == {
        "schema": "julia_core.context_admission.rejection.v1",
        "code": "test_rejection",
        "message": "exact precondition unavailable",
        "partial_admission": False,
    }


def test_production_surface_has_no_forbidden_dependency_or_marker() -> None:
    root = Path("julia_core/context_admission")
    forbidden_imports = {
        "julia_core.runtime",
        "julia_core.providers",
        "julia_core.assistant",
        "julia_core.context_os",
        "julia_core.persona",
    }
    forbidden_markers = (
        "fallback",
        "latest",
        "fuzzy",
        "successor",
        "mock",
        "stub",
        "shadow",
        "silent degrade",
        "best-effort",
    )

    for path in sorted(root.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        modules.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert modules & forbidden_imports == set()
        for marker in forbidden_markers:
            assert marker not in source.lower()


def test_p1_probe_remains_explicitly_non_authoritative() -> None:
    source = Path("tests/context_admission/c03_contract.py").read_text(encoding="utf-8")

    assert "not a production authority" in source
    assert "ExclusiveAdmissionProbe" in source
    assert C03_PRODUCTION_CONTRACT_VERSION.startswith(
        "julia_core.context_admission.c03.production"
    )
