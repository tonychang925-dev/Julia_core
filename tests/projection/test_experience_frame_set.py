from __future__ import annotations

import dataclasses
import hashlib
import json

import pytest

from julia_core.memory_experience import (
    MemoryExperienceRef,
    MemoryExperienceStatus,
    MemoryExperienceType,
    RelationshipExperienceContent,
)
from julia_core.projection import ExperienceFrame, ExperienceFrameSet


def frame(experience_id: str, version_id: str = "v1", event: str = "Event") -> ExperienceFrame:
    return ExperienceFrame(
        schema_version="1.0.0",
        policy_id="experience_projection.memory_experience_only",
        policy_version="1.0.0",
        source_ref=MemoryExperienceRef(experience_id, version_id),
        source_digest="a" * 64,
        source_status=MemoryExperienceStatus.CANDIDATE,
        experience_id=experience_id,
        version_id=version_id,
        predecessor_version_id=None,
        experience_type=MemoryExperienceType.RELATIONSHIP,
        content=RelationshipExperienceContent(
            relationship_id=f"relationship:{experience_id}",
            event=event,
            interpretation="Interpretation",
            occurred_at="2026-09-12T00:00:00Z",
        ).to_dict(),
        provenance_refs=(),
        created_at="2026-09-12T00:00:00Z",
    )


def carrier(*values: ExperienceFrame) -> ExperienceFrameSet:
    return ExperienceFrameSet(schema_version="1.0.0", frames=values)


def test_f1a_01_one_exact_experience_frame_accepted() -> None:
    single = frame("experience-1")

    assert carrier(single).frames == (single,)


def test_f1a_02_two_exact_experience_frames_accepted() -> None:
    left, right = frame("experience-1"), frame("experience-2")

    assert carrier(left, right).frames == (left, right)


def test_f1a_03_n_exact_frames_preserve_supplied_order() -> None:
    values = tuple(frame(f"experience-{index}") for index in range(6, 0, -1))

    assert carrier(*values).frames == values


def test_f1a_04_frames_remain_exact_tuple() -> None:
    values = (frame("experience-1"), frame("experience-2"))

    assert type(carrier(*values).frames) is tuple


def test_f1a_05_source_ref_preserved_exactly() -> None:
    values = (frame("experience-1", "version-1"), frame("experience-2", "version-2"))

    assert [item.source_ref for item in carrier(*values).frames] == [
        item.source_ref for item in values
    ]


def test_f1a_06_canonical_serialization_deterministic() -> None:
    values = (frame("experience-1"), frame("experience-2"))

    serialization = carrier(*values).canonical_serialization()
    assert serialization == carrier(*values).canonical_serialization()
    assert json.loads(serialization) == {
        "schema": "julia_core.projection.experience_frame_set.v1",
        "schema_version": "1.0.0",
        "frames": [item.to_dict() for item in values],
    }


def test_f1a_07_identical_carrier_produces_identical_digest() -> None:
    values = (frame("experience-1"), frame("experience-2"))

    assert carrier(*values).digest() == carrier(*values).digest()


def test_f1a_08_reversed_order_changes_serialization_and_digest() -> None:
    left, right = frame("experience-1"), frame("experience-2")
    ordered = carrier(left, right)
    reversed_order = carrier(right, left)

    assert ordered.frames != reversed_order.frames
    assert ordered.canonical_serialization() != reversed_order.canonical_serialization()
    assert ordered.digest() != reversed_order.digest()


def test_f1a_09_changed_contained_frame_changes_carrier_digest() -> None:
    original = carrier(frame("experience-1", event="Original"))
    changed = carrier(frame("experience-1", event="Changed"))

    assert original.digest() != changed.digest()


def test_f1a_10_one_frame_and_n_frames_use_same_contract() -> None:
    single = carrier(frame("experience-1"))
    multiple = carrier(frame("experience-1"), frame("experience-2"))

    assert type(single) is type(multiple) is ExperienceFrameSet
    assert single.to_dict()["schema"] == multiple.to_dict()["schema"]


def test_f1a_11_empty_tuple_rejected() -> None:
    with pytest.raises(ValueError, match="at least one"):
        carrier()


def test_f1a_12_list_rejected() -> None:
    with pytest.raises(TypeError, match="exact tuple"):
        ExperienceFrameSet(schema_version="1.0.0", frames=[frame("experience-1")])


def test_f1a_13_none_rejected() -> None:
    with pytest.raises(TypeError, match="exact tuple"):
        ExperienceFrameSet(schema_version="1.0.0", frames=None)


def test_f1a_14_raw_dict_frame_rejected() -> None:
    with pytest.raises(TypeError, match="exact ExperienceFrame"):
        ExperienceFrameSet(schema_version="1.0.0", frames=({"source_ref": "ref"},))


def test_f1a_15_experience_frame_subclass_rejected() -> None:
    class SubclassedFrame(ExperienceFrame):
        pass

    with pytest.raises(TypeError, match="exact ExperienceFrame"):
        base = frame("experience-1")
        ExperienceFrameSet(
            schema_version="1.0.0",
            frames=(
                SubclassedFrame(
                    schema_version=base.schema_version,
                    policy_id=base.policy_id,
                    policy_version=base.policy_version,
                    source_ref=base.source_ref,
                    source_digest=base.source_digest,
                    source_status=base.source_status,
                    experience_id=base.experience_id,
                    version_id=base.version_id,
                    predecessor_version_id=base.predecessor_version_id,
                    experience_type=base.experience_type,
                    content=base.content,
                    provenance_refs=base.provenance_refs,
                    created_at=base.created_at,
                ),
            ),
        )


def test_f1a_16_duplicate_exact_source_ref_rejected() -> None:
    duplicate_ref = MemoryExperienceRef("experience-1", "v1")
    left = frame("experience-1", event="Left")
    right = frame("experience-1", event="Right")
    object.__setattr__(right.source_ref, "experience_id", duplicate_ref.experience_id)

    with pytest.raises(ValueError, match="unique"):
        carrier(left, right)


def test_f1a_17_wrong_schema_version_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        ExperienceFrameSet(schema_version="1.0.1", frames=(frame("experience-1"),))


def test_f1a_18_post_construction_mutation_rejected() -> None:
    projected = carrier(frame("experience-1"))

    with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
        projected.frames = ()


def test_f1a_19_selection_api_absent() -> None:
    projected = carrier(frame("experience-1"), frame("experience-2"))

    assert not hasattr(projected, "first")
    assert not hasattr(projected, "latest")
    assert not hasattr(projected, "best")


def test_f1a_20_semantic_aggregation_api_absent() -> None:
    projected = carrier(frame("experience-1"), frame("experience-2"))

    assert not hasattr(projected, "merge")
    assert not hasattr(projected, "summarize")
    assert not hasattr(projected, "aggregate")


def test_digest_uses_canonical_utf8_serialization() -> None:
    projected = carrier(frame("experience-1"))

    assert projected.digest() == hashlib.sha256(
        projected.canonical_serialization().encode("utf-8")
    ).hexdigest()
