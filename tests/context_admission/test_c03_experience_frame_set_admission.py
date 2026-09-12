from __future__ import annotations

from dataclasses import fields, replace

import pytest

from julia_core.context_admission import (
    C03AdmissionRejected,
    ExclusiveAdmissionGate,
    ExclusiveAdmissionRequest,
    ModelVisibilityTransport,
)
from julia_core.memory_experience import MemoryExperienceRef
from julia_core.projection import ExperienceFrame, ExperienceFrameSet

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


def request(experiences: ExperienceFrameSet | None = None) -> ExclusiveAdmissionRequest:
    return ExclusiveAdmissionRequest(
        identity_frame=canonical_identity_frame(),
        experience_frames=experiences if experiences is not None else experience_set(),
        current_task_context=canonical_current_task_context(),
    )


def forged(package, **changes):
    result = object.__new__(type(package))
    for field in fields(type(package)):
        object.__setattr__(result, field.name, getattr(package, field.name))
    for name, value in changes.items():
        object.__setattr__(result, name, value)
    return result


def test_f1b_01_one_frame_experience_frame_set_admitted() -> None:
    sealed = ExclusiveAdmissionGate().seal(request(experience_set(1)))

    assert sealed.experience_frame_count == 1
    assert len(sealed.experience_frame_digests) == 1


def test_f1b_02_two_frame_experience_frame_set_admitted() -> None:
    sealed = ExclusiveAdmissionGate().seal(request(experience_set(2)))

    assert sealed.experience_frame_count == 2
    assert len(sealed.experience_frame_digests) == 2


def test_f1b_03_n_frame_experience_frame_set_admitted() -> None:
    experiences = experience_set(6)

    sealed = ExclusiveAdmissionGate().seal(request(experiences))

    assert sealed.experience_frame_count == len(experiences.frames)


def test_f1b_04_carrier_digest_preserved_exactly() -> None:
    experiences = experience_set(3)

    sealed = ExclusiveAdmissionGate().seal(request(experiences))

    assert sealed.experience_digest == experiences.digest()
    assert sealed.admitted_frames["experience_frame_set"] == experiences.digest()


def test_f1b_05_all_individual_frame_digests_manifested() -> None:
    experiences = experience_set(4)

    sealed = ExclusiveAdmissionGate().seal(request(experiences))

    assert sealed.experience_frame_digests == tuple(
        frame.digest() for frame in experiences.frames
    )


def test_f1b_06_frame_digest_order_preserved() -> None:
    experiences = experience_set(4)

    sealed = ExclusiveAdmissionGate().seal(request(experiences))

    assert list(sealed.experience_frame_digests) == [frame.digest() for frame in experiences.frames]


def test_f1b_07_identity_frame_remains_exact() -> None:
    identity = canonical_identity_frame()

    sealed = ExclusiveAdmissionGate().seal(
        ExclusiveAdmissionRequest(
            identity_frame=identity,
            experience_frames=experience_set(),
            current_task_context=canonical_current_task_context(),
        )
    )

    assert sealed.identity_digest == identity.digest()


def test_f1b_08_current_task_remains_exact() -> None:
    current_task = canonical_current_task_context()

    sealed = ExclusiveAdmissionGate().seal(
        ExclusiveAdmissionRequest(
            identity_frame=canonical_identity_frame(),
            experience_frames=experience_set(2),
            current_task_context=current_task,
        )
    )

    assert sealed.current_task_digest == current_task.digest()
    assert sealed.conversation_id == current_task.conversation_id
    assert sealed.turn_id == current_task.turn_id


def test_f1b_09_package_verification_succeeds() -> None:
    sealed = ExclusiveAdmissionGate().seal(request(experience_set(3)))

    assert sealed.verify() is sealed
    assert ModelVisibilityTransport().render(sealed)["gate_receipt"] == sealed.gate_receipt


def test_f1b_10_one_and_n_experiences_use_same_c03_path() -> None:
    one = ExclusiveAdmissionGate().seal(request(experience_set(1)))
    many = ExclusiveAdmissionGate().seal(request(experience_set(5)))

    assert type(one) is type(many)
    assert one.contract_version == many.contract_version
    assert one.to_dict()["source_digests"].keys() == many.to_dict()["source_digests"].keys()


def test_f1b_11_singular_experience_frame_request_surface_absent() -> None:
    assert "experience_frame" not in ExclusiveAdmissionRequest.__dataclass_fields__

    with pytest.raises(TypeError):
        ExclusiveAdmissionRequest(
            identity_frame=canonical_identity_frame(),
            experience_frame=canonical_experience_frame(),
            current_task_context=canonical_current_task_context(),
        )


def test_f1b_12_none_carrier_rejected() -> None:
    with pytest.raises(C03AdmissionRejected, match="ExperienceFrameSet"):
        ExclusiveAdmissionRequest(
            identity_frame=canonical_identity_frame(),
            experience_frames=None,
            current_task_context=canonical_current_task_context(),
        )


def test_f1b_13_wrong_carrier_type_rejected() -> None:
    with pytest.raises(C03AdmissionRejected, match="ExperienceFrameSet"):
        ExclusiveAdmissionRequest(
            identity_frame=canonical_identity_frame(),
            experience_frames=canonical_experience_frame(),
            current_task_context=canonical_current_task_context(),
        )


def test_f1b_14_carrier_subclass_rejected() -> None:
    class SubclassedFrameSet(ExperienceFrameSet):
        pass

    with pytest.raises(C03AdmissionRejected, match="ExperienceFrameSet"):
        ExclusiveAdmissionRequest(
            identity_frame=canonical_identity_frame(),
            experience_frames=SubclassedFrameSet(
                schema_version="1.0.0",
                frames=experience_set().frames,
            ),
            current_task_context=canonical_current_task_context(),
        )


def test_f1b_15_corrupted_frame_set_digest_relation_fails() -> None:
    sealed = ExclusiveAdmissionGate().seal(request(experience_set(2)))

    with pytest.raises(C03AdmissionRejected):
        forged(sealed, experience_digest="d" * 64).verify()


def test_f1b_16_missing_individual_frame_digest_fails() -> None:
    sealed = ExclusiveAdmissionGate().seal(request(experience_set(2)))

    with pytest.raises(C03AdmissionRejected, match="count does not match"):
        forged(sealed, experience_frame_digests=sealed.experience_frame_digests[:1]).verify()


def test_f1b_17_reordered_frame_digest_manifest_fails() -> None:
    sealed = ExclusiveAdmissionGate().seal(request(experience_set(2)))
    reordered = tuple(reversed(sealed.experience_frame_digests))

    with pytest.raises(C03AdmissionRejected, match="receipt"):
        forged(sealed, experience_frame_digests=reordered).verify()


def test_f1b_18_frame_loss_fails() -> None:
    sealed = ExclusiveAdmissionGate().seal(request(experience_set(3)))

    with pytest.raises(C03AdmissionRejected, match="receipt"):
        forged(
            sealed,
            experience_frame_digests=sealed.experience_frame_digests[:2],
            experience_frame_count=2,
        ).verify()


def test_f1b_19_no_selection_surface() -> None:
    assert not hasattr(ExclusiveAdmissionGate, "first")
    assert not hasattr(ExclusiveAdmissionGate, "latest")
    assert not hasattr(ExperienceFrameSet, "best")


def test_f1b_20_no_compatibility_singular_path() -> None:
    production_source = (
        __import__("inspect").getsource(ExclusiveAdmissionGate)
        + __import__("inspect").getsource(ExclusiveAdmissionRequest)
    )

    assert "experience_frame=" not in production_source
    assert "len(experience_frames.frames) == 1" not in production_source
