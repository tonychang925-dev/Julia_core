from __future__ import annotations

from dataclasses import fields
from hashlib import sha256

import pytest

from julia_core.context_admission import (
    AdmittedSemanticBundle,
    C03AdmissionRejected,
    CurrentConversationalTaskContext,
    ExactAdmittedSemanticBinder,
    ExclusiveAdmissionGate,
    SealedCognitiveContextPackage,
    SemanticBindingRequest,
)
from julia_core.context_admission.contracts import canonical_json
from julia_core.projection.contracts import ExperienceFrame, IdentityFrame
from tests.context_admission.production_fixtures import (
    canonical_current_task_context,
    canonical_experience_frame,
    canonical_identity_frame,
    canonical_request,
)
from julia_core.context_admission.semantic_binding import _BINDER_ISSUER


def bound_inputs(*, turn_id: str = "turn-eng12a-1"):
    request = canonical_request(
        current_task=canonical_current_task_context(turn_id=turn_id)
    )
    package = ExclusiveAdmissionGate().seal(request)
    return (
        package,
        request.identity_frame,
        request.experience_frame,
        request.current_task_context,
    )


def bound_bundle():
    return ExactAdmittedSemanticBinder().bind(SemanticBindingRequest(*bound_inputs()))


def test_binder_produces_exact_ordered_units_and_roles():
    binding = bound_bundle()

    assert [unit.frame_name for unit in binding.units] == [
        "identity_frame",
        "experience_frame",
        "current_task_context",
    ]
    assert [unit.role for unit in binding.units] == ["system", "system", "user"]
    assert tuple(binding.package_digest_manifest) == (
        "identity_frame",
        "experience_frame",
        "current_task_context",
    )
    assert binding.conversation_id == "conversation-eng12a"
    assert binding.turn_id == "turn-eng12a-1"
    assert len(binding.gate_receipt) == 64


def test_semantic_fingerprint_covers_exact_bound_messages_deterministically():
    first = bound_bundle()
    second = bound_bundle()
    expected = sha256(
        canonical_json([unit.to_message() for unit in first.units]).encode("utf-8")
    ).hexdigest()

    assert first.semantic_fingerprint() == expected
    assert first.semantic_fingerprint() == second.semantic_fingerprint()


def test_package_is_verified_before_semantic_content_is_bound():
    class PoisonFrame(IdentityFrame):
        def to_dict(self):
            raise AssertionError("semantic content read before package verification")

    package, identity, experience, current_task = bound_inputs()
    poison = PoisonFrame(
        schema_version=identity.schema_version,
        policy_id=identity.policy_id,
        policy_version=identity.policy_version,
        source_ref=identity.source_ref,
        source_digest=identity.source_digest,
        source_status=identity.source_status,
        identity_id=identity.identity_id,
        predecessor_version_id=identity.predecessor_version_id,
        anchors=identity.anchors,
        values=identity.values,
        boundaries=identity.boundaries,
        relationship_role_anchors=identity.relationship_role_anchors,
        provenance_refs=identity.provenance_refs,
    )
    forged = object.__new__(SealedCognitiveContextPackage)
    for field in fields(SealedCognitiveContextPackage):
        object.__setattr__(forged, field.name, getattr(package, field.name))
    object.__setattr__(forged, "gate_receipt", "0" * 64)

    with pytest.raises(C03AdmissionRejected, match="receipt"):
        SemanticBindingRequest(forged, poison, experience, current_task)


@pytest.mark.parametrize(
    ("frame_name", "frame_type"),
    [
        ("identity_frame", IdentityFrame),
        ("experience_frame", ExperienceFrame),
        ("current_task_context", CurrentConversationalTaskContext),
    ],
)
def test_exact_frame_types_are_required(frame_name, frame_type):
    values = bound_inputs()
    arguments = list(values)
    arguments[1 + ("identity_frame", "experience_frame", "current_task_context").index(frame_name)] = object()

    expected_message = {
        "identity_frame": "exact canonical IdentityFrame",
        "experience_frame": "exact canonical ExperienceFrame",
        "current_task_context": "exact canonical current task context",
    }[frame_name]
    with pytest.raises(C03AdmissionRejected, match=expected_message):
        SemanticBindingRequest(*arguments)
    assert frame_type


def test_changed_admitted_frame_fails_against_package_manifest():
    package, identity, experience, current_task = bound_inputs()
    object.__setattr__(
        experience,
        "content",
        {"commitment": "post-seal semantic mutation"},
    )

    with pytest.raises(C03AdmissionRejected, match="does not match the sealed package"):
        ExactAdmittedSemanticBinder().bind(
            SemanticBindingRequest(package, identity, experience, current_task)
        )


def test_stale_conversation_or_turn_fails_closed():
    package, identity, experience, _ = bound_inputs()
    stale = canonical_current_task_context(turn_id="turn-eng12a-2")

    with pytest.raises(C03AdmissionRejected, match="turn does not match"):
        ExactAdmittedSemanticBinder().bind(
            SemanticBindingRequest(package, identity, experience, stale)
        )


def test_name_forged_package_cannot_enter_binding():
    package, identity, experience, current_task = bound_inputs()
    forged = object.__new__(type("SealedCognitiveContextPackage", (), {}))
    forged.__module__ = SealedCognitiveContextPackage.__module__

    with pytest.raises(C03AdmissionRejected, match="exact sealed C03 package"):
        SemanticBindingRequest(forged, identity, experience, current_task)


def test_only_exact_binder_constructs_production_bundle_and_units():
    binding = bound_bundle()
    bundle_arguments = {
        field.name: getattr(binding, field.name)
        for field in fields(AdmittedSemanticBundle)
        if field.name != "issued_by"
    }

    with pytest.raises(C03AdmissionRejected, match="only ExactAdmittedSemanticBinder"):
        AdmittedSemanticBundle(**bundle_arguments, issued_by=object())


def test_incomplete_or_ambiguous_bundle_cannot_be_minted():
    binding = bound_bundle()
    arguments = {
        field.name: getattr(binding, field.name)
        for field in fields(AdmittedSemanticBundle)
        if field.name != "issued_by"
    }
    arguments["units"] = binding.units[:2]

    with pytest.raises(C03AdmissionRejected, match="all three"):
        AdmittedSemanticBundle(**arguments, issued_by=_BINDER_ISSUER)
