from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from julia_core.identity import IdentityStatus
from julia_core.memory_experience import MemoryExperienceStatus
from julia_core.projection.contracts import ExperienceFrameSet, IdentityFrame

from julia_core.context_admission import (
    C03AdmissionRejected,
    CanonicalConversationProvenance,
    CanonicalConversationSource,
    CurrentConversationalTaskContext,
    ExclusiveAdmissionRequest,
    ExclusiveAdmissionGate,
    ModelVisibilityTransport,
    SealedCognitiveContextPackage,
)
from tests.context_admission.c03_contract import C03_CONTRACT_VERSION
from tests.context_admission.production_fixtures import (
    canonical_current_task_context,
    canonical_experience_frame,
    canonical_experience_frame_set,
    canonical_identity_frame,
    canonical_request,
)


def test_c03_01_admits_only_exact_canonical_frames() -> None:
    class SubclassedIdentityFrame(IdentityFrame):
        pass

    canonical_identity = canonical_identity_frame()
    subclassed_identity = SubclassedIdentityFrame(
        schema_version=canonical_identity.schema_version,
        policy_id=canonical_identity.policy_id,
        policy_version=canonical_identity.policy_version,
        source_ref=canonical_identity.source_ref,
        source_digest=canonical_identity.source_digest,
        source_status=canonical_identity.source_status,
        identity_id=canonical_identity.identity_id,
        predecessor_version_id=canonical_identity.predecessor_version_id,
        anchors=canonical_identity.anchors,
        values=canonical_identity.values,
        boundaries=canonical_identity.boundaries,
        relationship_role_anchors=canonical_identity.relationship_role_anchors,
        provenance_refs=canonical_identity.provenance_refs,
    )

    with pytest.raises(C03AdmissionRejected, match="exact canonical IdentityFrame"):
        ExclusiveAdmissionRequest(
            identity_frame=subclassed_identity,
            experience_frames=canonical_experience_frame_set(),
            current_task_context=canonical_current_task_context(),
        )

    package = ExclusiveAdmissionGate().seal(canonical_request())
    assert set(package.admitted_frames) == {
        "identity_frame",
        "experience_frame_set",
        "current_task_context",
    }
    assert package.experience_frame_count == 1
    assert package.experience_frame_digests == (
        canonical_experience_frame().digest(),
    )


def test_c03_02_rejects_raw_memory_as_admission_authority() -> None:
    raw_memory = {
        "authority": "raw_memory",
        "content": "Remember this outside the canonical frame contract",
    }

    with pytest.raises(C03AdmissionRejected, match="exact canonical ExperienceFrameSet"):
        ExclusiveAdmissionRequest(
            identity_frame=canonical_identity_frame(),
            experience_frames=raw_memory,
            current_task_context=canonical_current_task_context(),
        )
    with pytest.raises(C03AdmissionRejected, match="sealed C03 package"):
        ModelVisibilityTransport().render(raw_memory)


def test_c03_03_persona_package_cannot_mint_authority() -> None:
    sealed = ExclusiveAdmissionGate().seal(canonical_request())
    payload = sealed.to_dict()

    assert payload["authority"] == {
        "canonical": False,
        "runtime": False,
        "provider": False,
        "assistant_self": False,
    }
    assert isinstance(sealed, MemoryExperienceStatus) is False
    with pytest.raises((TypeError, ValueError)):
        MemoryExperienceStatus(sealed)


def test_c03_04_rejects_assistant_self_block_as_authority() -> None:
    assistant_self_block = {
        "source": "assistant_self_observation",
        "authority": "canonical_identity",
        "statement": "Assistant believes this fact is canonical",
    }

    with pytest.raises(C03AdmissionRejected, match="exact canonical IdentityFrame"):
        ExclusiveAdmissionRequest(
            identity_frame=assistant_self_block,
            experience_frames=canonical_experience_frame_set(),
            current_task_context=canonical_current_task_context(),
        )
    with pytest.raises(C03AdmissionRejected, match="sealed C03 package"):
        ModelVisibilityTransport().render(assistant_self_block)


def test_c03_05_rejects_provider_persona_prompt_as_admission() -> None:
    provider_prompt = {
        "source": "provider_system_prompt",
        "identity": "You are Julia",
        "memory": "Use this unverified persona narrative",
    }

    with pytest.raises(C03AdmissionRejected, match="exact canonical current task context"):
        ExclusiveAdmissionRequest(
            identity_frame=canonical_identity_frame(),
            experience_frames=canonical_experience_frame_set(),
            current_task_context=provider_prompt,
        )
    with pytest.raises(C03AdmissionRejected, match="sealed C03 package"):
        ModelVisibilityTransport().render(provider_prompt)


def test_c03_06_model_visibility_requires_c03_gate() -> None:
    identity = canonical_identity_frame()
    experiences = canonical_experience_frame_set()
    current_task = canonical_current_task_context()

    for bypass in (identity, experiences, current_task, canonical_request()):
        with pytest.raises(C03AdmissionRejected, match="sealed C03 package"):
            ModelVisibilityTransport().render(bypass)

    sealed = ExclusiveAdmissionGate().seal(canonical_request())
    rendered = ModelVisibilityTransport().render(sealed)
    assert rendered["gate_receipt"] == sealed.gate_receipt


def test_c03_07_rejects_partial_admission() -> None:
    with pytest.raises(C03AdmissionRejected, match="exact canonical IdentityFrame"):
        ExclusiveAdmissionRequest(
            identity_frame=None,
            experience_frames=canonical_experience_frame_set(),
            current_task_context=canonical_current_task_context(),
        )
    with pytest.raises(C03AdmissionRejected, match="exact canonical ExperienceFrameSet"):
        ExclusiveAdmissionRequest(
            identity_frame=canonical_identity_frame(),
            experience_frames=None,
            current_task_context=canonical_current_task_context(),
        )
    with pytest.raises(C03AdmissionRejected, match="exact canonical current task context"):
        ExclusiveAdmissionRequest(
            identity_frame=canonical_identity_frame(),
            experience_frames=canonical_experience_frame_set(),
            current_task_context=None,
        )


@pytest.mark.parametrize(
    ("admission_request", "message"),
    [
        (
            canonical_request(
                identity=replace(canonical_identity_frame(), source_digest="not-a-digest")
            ),
            "identity source digest is absent or inexact",
        ),
        (
            canonical_request(identity=canonical_identity_frame(provenance_refs=())),
            "identity frame provenance is absent",
        ),
        (
            canonical_request(
                identity=replace(
                    canonical_identity_frame(), source_status=IdentityStatus.CANDIDATE
                )
            ),
            "identity source is not admitted",
        ),
        (
            canonical_request(
                experiences=ExperienceFrameSet(
                    schema_version="1.0.0",
                    frames=(canonical_experience_frame(provenance_refs=()),),
                )
            ),
            "experience frame provenance is absent",
        ),
        (
            canonical_request(
                experiences=ExperienceFrameSet(
                    schema_version="1.0.0",
                    frames=(
                        replace(
                            canonical_experience_frame(),
                            source_status=MemoryExperienceStatus.CANDIDATE,
                        ),
                    ),
                )
            ),
            "experience source is not admitted",
        ),
    ],
)
def test_c03_08_missing_or_inexact_provenance_fails_closed(admission_request, message) -> None:
    with pytest.raises(C03AdmissionRejected, match=message):
        ExclusiveAdmissionGate().seal(admission_request)

    with pytest.raises(C03AdmissionRejected, match="digest is absent or inexact"):
        replace(
            canonical_current_task_context(),
            provenance=CanonicalConversationProvenance(
                source_type=CanonicalConversationSource.CONVERSATION_RUNTIME,
                source_ref="conversation_runtime://eng12a/current-task",
                source_digest="missing",
                observed_at="2026-09-12T00:00:00Z",
            ),
        )


def test_c03_09_current_task_context_is_bounded() -> None:
    oversized = {
        "surface": "x" * 2048,
        "details": {"nested": {"value": "further exceeds the bounded budget"}},
    }

    with pytest.raises(C03AdmissionRejected, match="bounded-state budget"):
        canonical_current_task_context(bounded_state=oversized)
    with pytest.raises(C03AdmissionRejected, match="bounded-state depth"):
        canonical_current_task_context(
            bounded_state={"level_1": {"level_2": {"level_3": {"level_4": "too deep"}}}}
        )

    context = canonical_current_task_context()
    assert set(context.to_dict()) == {
        "schema",
        "schema_version",
        "conversation_id",
        "turn_id",
        "task_intent",
        "task_domain",
        "current_modality",
        "bounded_state",
        "provenance",
        "canonical_authority",
        "runtime_authority",
    }


def test_c03_10_sealed_package_is_immutable() -> None:
    identity = canonical_identity_frame()
    experiences = canonical_experience_frame_set()
    current_task = canonical_current_task_context()
    request = ExclusiveAdmissionRequest(identity, experiences, current_task)
    identity_digest = identity.digest()
    experience_digest = experiences.digest()
    current_task_digest = current_task.digest()
    sealed = ExclusiveAdmissionGate().seal(request)

    with pytest.raises(FrozenInstanceError):
        sealed.turn_id = "changed"
    with pytest.raises(TypeError):
        sealed.admitted_frames["identity_frame"] = "changed"
    with pytest.raises(AttributeError):
        object.__setattr__(sealed, "runtime_authority", True)

    assert identity.digest() == identity_digest
    assert experiences.digest() == experience_digest
    assert current_task.digest() == current_task_digest


def test_c03_11_gate_receipt_is_deterministic_for_equivalent_input() -> None:
    first = ExclusiveAdmissionGate().seal(canonical_request())
    second = ExclusiveAdmissionGate().seal(canonical_request())
    changed_task = ExclusiveAdmissionGate().seal(
        canonical_request(current_task=canonical_current_task_context(turn_id="turn-2"))
    )

    assert first.gate_receipt == second.gate_receipt
    assert first.to_dict() == second.to_dict()
    assert changed_task.gate_receipt != first.gate_receipt
    assert len(first.gate_receipt) == 64


def test_c03_12_package_does_not_mint_runtime_authority() -> None:
    sealed = ExclusiveAdmissionGate().seal(canonical_request())
    payload = ModelVisibilityTransport().render(sealed)

    assert payload["authority"]["runtime"] is False
    assert payload["authority"]["canonical"] is False
    assert not hasattr(sealed, "runtime_authority")
    assert not hasattr(sealed, "capability_authority")
    assert not isinstance(sealed, CurrentConversationalTaskContext)

    forged = object.__new__(SealedCognitiveContextPackage)
    for name, value in sealed.__dataclass_fields__.items():
        object.__setattr__(forged, name, getattr(sealed, name))
    object.__setattr__(forged, "gate_receipt", "0" * 64)
    with pytest.raises(C03AdmissionRejected, match="receipt is forged"):
        ModelVisibilityTransport().render(forged)


def test_fixture_contract_exactly_names_frozen_direction_and_non_production_status() -> None:
    fixture = json.loads(
        Path(__file__).parents[1].joinpath("fixtures", "c03", "canonical_source_contract.json").read_text()
    )

    assert fixture["contract_version"] == C03_CONTRACT_VERSION
    assert fixture["canonical_inputs"] == [
        "IdentityFrame",
        "ExperienceFrameSet",
        "CurrentConversationalTaskContext",
    ]
    assert fixture["exclusive_direction"] == [
        "IdentityFrame + ExperienceFrameSet + CurrentConversationalTaskContext",
        "Exclusive Admission Gate",
        "sealed CognitiveContextPackage",
        "STOP",
    ]
    assert fixture["test_only"] is True
    assert fixture["production_implementation"] is False
