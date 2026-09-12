from __future__ import annotations

import inspect
from dataclasses import fields, replace
from hashlib import sha256

import pytest

from julia_core.context_admission import (
    C03AdmissionRejected,
    ExactAdmittedSemanticBinder,
    ExclusiveAdmissionGate,
    ExclusiveAdmissionRequest,
    SemanticBindingRequest,
)
from julia_core.context_admission.contracts import canonical_json, package_digest
from julia_core.memory_experience import MemoryExperienceRef
from julia_core.projection import ExperienceFrameSet

from .production_fixtures import (
    canonical_current_task_context,
    canonical_experience_frame,
    canonical_identity_frame,
)


def experience_set(count: int = 1) -> ExperienceFrameSet:
    values = []
    for index in range(1, count + 1):
        frame = canonical_experience_frame()
        if index > 1:
            frame = replace(
                frame,
                source_ref=MemoryExperienceRef(f"experience-eng12a-{index}", "v1"),
            )
        values.append(frame)
    return ExperienceFrameSet(schema_version="1.0.0", frames=tuple(values))


def binding_inputs(
    experiences: ExperienceFrameSet | None = None,
) -> tuple[ExclusiveAdmissionRequest, SemanticBindingRequest]:
    values = experiences if experiences is not None else experience_set()
    request = ExclusiveAdmissionRequest(
        identity_frame=canonical_identity_frame(),
        experience_frames=values,
        current_task_context=canonical_current_task_context(),
    )
    package = ExclusiveAdmissionGate().seal(request)
    return request, SemanticBindingRequest(
        package,
        request.identity_frame,
        request.experience_frames,
        request.current_task_context,
    )


def bind(count: int = 1):
    _, binding_request = binding_inputs(experience_set(count))
    return ExactAdmittedSemanticBinder().bind(binding_request)


def forged_package(binding_request: SemanticBindingRequest, **changes):
    package = binding_request.package
    forged = object.__new__(type(package))
    for field in fields(type(package)):
        object.__setattr__(forged, field.name, getattr(package, field.name))
    for name, value in changes.items():
        object.__setattr__(forged, name, value)
    admitted = dict(package.admitted_frames)
    if "experience_digest" in changes:
        admitted["experience_frame_set"] = changes["experience_digest"]
    object.__setattr__(forged, "admitted_frames", admitted)
    receipt = package_digest(
        forged.contract_version,
        forged.conversation_id,
        forged.turn_id,
        forged.identity_digest,
        forged.experience_digest,
        forged.experience_frame_digests,
        forged.experience_frame_count,
        forged.current_task_digest,
    )
    object.__setattr__(forged, "gate_receipt", receipt)
    return forged


def rebound(binding_request: SemanticBindingRequest, package):
    return ExactAdmittedSemanticBinder().bind(
        SemanticBindingRequest(
            package,
            binding_request.identity_frame,
            binding_request.experience_frames,
            binding_request.current_task_context,
        )
    )


def test_f1c_01_one_frame_set_binds() -> None:
    assert bind(1).units[1].frame_name == "experience_frame_set"


def test_f1c_02_two_frame_set_binds() -> None:
    assert bind(2).units[1].frame_name == "experience_frame_set"


def test_f1c_03_n_frame_set_binds() -> None:
    assert bind(5).units[1].frame_name == "experience_frame_set"


def test_f1c_04_exact_carrier_digest_matches_sealed_package() -> None:
    experiences = experience_set(3)
    _, binding_request = binding_inputs(experiences)
    binding = ExactAdmittedSemanticBinder().bind(binding_request)

    assert binding.package_digest_manifest["experience_frame_set"] == experiences.digest()


def test_f1c_05_exact_individual_frame_digest_manifest_matches() -> None:
    experiences = experience_set(3)
    _, binding_request = binding_inputs(experiences)

    assert binding_request.package.experience_frame_digests == tuple(
        frame.digest() for frame in experiences.frames
    )


def test_f1c_06_frame_count_preserved() -> None:
    experiences = experience_set(4)
    _, binding_request = binding_inputs(experiences)
    ExactAdmittedSemanticBinder().bind(binding_request)

    assert binding_request.package.experience_frame_count == len(experiences.frames)


def test_f1c_07_frame_order_preserved() -> None:
    experiences = experience_set(4)
    _, binding_request = binding_inputs(experiences)
    ExactAdmittedSemanticBinder().bind(binding_request)

    assert binding_request.package.experience_frame_digests == tuple(
        frame.digest() for frame in experiences.frames
    )


def test_f1c_08_canonical_frame_set_json_becomes_one_system_unit() -> None:
    experiences = experience_set(3)
    _, binding_request = binding_inputs(experiences)
    binding = ExactAdmittedSemanticBinder().bind(binding_request)
    unit = binding.units[1]

    assert unit.role == "system"
    assert unit.canonical_content == canonical_json(experiences.to_dict())


def test_f1c_09_exactly_three_semantic_units_remain() -> None:
    binding = bind(4)

    assert [unit.frame_name for unit in binding.units] == [
        "identity_frame",
        "experience_frame_set",
        "current_task_context",
    ]


def test_f1c_10_semantic_fingerprint_deterministic() -> None:
    first = bind(3)
    second = bind(3)
    expected = sha256(
        canonical_json([unit.to_message() for unit in first.units]).encode("utf-8")
    ).hexdigest()

    assert first.semantic_fingerprint() == expected
    assert first.semantic_fingerprint() == second.semantic_fingerprint()


def test_f1c_11_one_and_n_use_same_binder_path() -> None:
    one = bind(1)
    many = bind(5)

    assert type(one) is type(many)
    assert [unit.frame_name for unit in one.units] == [
        unit.frame_name for unit in many.units
    ]


def test_f1c_12_singular_experience_frame_rejected() -> None:
    _, binding_request = binding_inputs()

    with pytest.raises(C03AdmissionRejected, match="ExperienceFrameSet"):
        SemanticBindingRequest(
            binding_request.package,
            binding_request.identity_frame,
            canonical_experience_frame(),
            binding_request.current_task_context,
        )


def test_f1c_13_raw_dict_rejected() -> None:
    _, binding_request = binding_inputs()

    with pytest.raises(C03AdmissionRejected, match="ExperienceFrameSet"):
        SemanticBindingRequest(
            binding_request.package,
            binding_request.identity_frame,
            {"frames": []},
            binding_request.current_task_context,
        )


def test_f1c_14_experience_frame_set_subclass_rejected() -> None:
    class SubclassedFrameSet(ExperienceFrameSet):
        pass

    _, binding_request = binding_inputs()

    with pytest.raises(C03AdmissionRejected, match="ExperienceFrameSet"):
        SemanticBindingRequest(
            binding_request.package,
            binding_request.identity_frame,
            SubclassedFrameSet(
                schema_version="1.0.0",
                frames=binding_request.experience_frames.frames,
            ),
            binding_request.current_task_context,
        )


def test_f1c_15_carrier_digest_mismatch_rejected() -> None:
    _, binding_request = binding_inputs(experience_set(2))
    forged = forged_package(binding_request, experience_digest="d" * 64)

    with pytest.raises(C03AdmissionRejected, match="does not match the sealed package"):
        rebound(binding_request, forged)


def test_f1c_16_individual_frame_digest_mismatch_rejected() -> None:
    _, binding_request = binding_inputs(experience_set(2))
    manifest = binding_request.package.experience_frame_digests
    forged = forged_package(
        binding_request,
        experience_frame_digests=("d" * 64, manifest[1]),
    )

    with pytest.raises(C03AdmissionRejected, match="manifest does not match"):
        rebound(binding_request, forged)


def test_f1c_17_frame_count_mismatch_rejected() -> None:
    _, binding_request = binding_inputs(experience_set(2))
    forged = forged_package(binding_request, experience_frame_count=1)

    with pytest.raises(C03AdmissionRejected, match="count does not match"):
        SemanticBindingRequest(
            forged,
            binding_request.identity_frame,
            binding_request.experience_frames,
            binding_request.current_task_context,
        )


def test_f1c_18_reordered_frame_digest_manifest_rejected() -> None:
    _, binding_request = binding_inputs(experience_set(2))
    forged = forged_package(
        binding_request,
        experience_frame_digests=tuple(
            reversed(binding_request.package.experience_frame_digests)
        ),
    )

    with pytest.raises(C03AdmissionRejected, match="manifest does not match"):
        rebound(binding_request, forged)


def test_f1c_19_frame_loss_rejected() -> None:
    _, binding_request = binding_inputs(experience_set(3))
    forged = forged_package(
        binding_request,
        experience_frame_digests=binding_request.package.experience_frame_digests[:2],
        experience_frame_count=2,
    )

    with pytest.raises(C03AdmissionRejected, match="manifest does not match"):
        rebound(binding_request, forged)


def test_f1c_20_no_singular_compatibility_surface() -> None:
    assert "experience_frame" not in SemanticBindingRequest.__dataclass_fields__


def test_f1c_21_no_selection_api_or_branch() -> None:
    source = inspect.getsource(ExactAdmittedSemanticBinder)

    assert "frames[0]" not in source
    assert "len(request.experience_frames.frames) == 1" not in source
