from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from julia_core.memory_experience import (
    MemoryExperienceRef,
    MemoryExperienceStatus,
    MemoryExperienceType,
)
from julia_core.projection import ExperienceFrame, ExperienceFrameSet


SOURCE_PATH = Path("julia_core/projection/contracts.py")


def frame(experience_id: str, content: str | None = None) -> ExperienceFrame:
    return ExperienceFrame(
        schema_version="1.0.0",
        policy_id="experience_projection.memory_experience_only",
        policy_version="1.0.0",
        source_ref=MemoryExperienceRef(experience_id, "v1"),
        source_digest="a" * 64,
        source_status=MemoryExperienceStatus.ADMITTED,
        experience_id=experience_id,
        version_id="v1",
        predecessor_version_id=None,
        experience_type=MemoryExperienceType.PROJECT_COMMITMENT,
        content={"commitment": content or f"commitment-{experience_id}"},
        provenance_refs=(
            {
                "source_ref": f"memory://{experience_id}/v1",
                "source_digest": "a" * 64,
            },
        ),
        created_at="2026-09-12T00:00:00Z",
    )


def frame_set(*frames: ExperienceFrame) -> ExperienceFrameSet:
    return ExperienceFrameSet(schema_version="1.0.0", frames=tuple(frames))


def test_f1a_01_one_exact_frame_is_accepted() -> None:
    source = frame("experience-one")
    carrier = frame_set(source)

    assert carrier.frames == (source,)


def test_f1a_02_two_exact_frames_are_accepted() -> None:
    sources = (frame("experience-one"), frame("experience-two"))
    carrier = frame_set(*sources)

    assert carrier.frames == sources


def test_f1a_03_n_frames_preserve_exact_order() -> None:
    sources = tuple(frame(f"experience-{index}") for index in range(12))
    carrier = frame_set(*sources)

    assert tuple(item.source_ref for item in carrier.frames) == tuple(
        item.source_ref for item in sources
    )
    assert [item["experience_id"] for item in carrier.to_dict()["frames"]] == [
        item.experience_id for item in sources
    ]


def test_f1a_04_tuple_is_retained_immutably() -> None:
    carrier = frame_set(frame("experience-one"))

    assert type(carrier.frames) is tuple
    with pytest.raises(FrozenInstanceError):
        carrier.frames = ()


def test_f1a_05_exact_source_refs_are_preserved() -> None:
    sources = (frame("experience-one"), frame("experience-two"))
    carrier = frame_set(*sources)

    assert tuple(item.source_ref for item in carrier.frames) == tuple(
        item.source_ref for item in sources
    )


def test_f1a_06_and_f1a_07_serialization_and_digest_are_deterministic() -> None:
    carrier = frame_set(frame("experience-one"), frame("experience-two"))
    same_carrier = frame_set(frame("experience-one"), frame("experience-two"))

    assert carrier.canonical_serialization() == same_carrier.canonical_serialization()
    assert carrier.digest() == same_carrier.digest()


def test_f1a_08_order_change_changes_serialization_and_digest() -> None:
    first = frame("experience-one")
    second = frame("experience-two")

    assert frame_set(first, second).canonical_serialization() != frame_set(
        second, first
    ).canonical_serialization()
    assert frame_set(first, second).digest() != frame_set(second, first).digest()


def test_f1a_09_frame_content_change_changes_digest() -> None:
    original = frame_set(frame("experience-one", content="original"))
    changed = frame_set(frame("experience-one", content="changed"))

    assert original.digest() != changed.digest()


def test_f1a_10_one_frame_and_n_frames_use_one_contract() -> None:
    one = frame_set(frame("experience-one"))
    many = frame_set(frame("experience-one"), frame("experience-two"))

    assert type(one) is type(many) is ExperienceFrameSet
    assert one.to_dict()["schema"] == many.to_dict()["schema"]


@pytest.mark.parametrize(
    ("frames", "message"),
    [
        ((), "nonempty frame tuple"),
        ([frame("experience-one")], "nonempty frame tuple"),
        (None, "nonempty frame tuple"),
        ({"experience-one": frame("experience-one")}, "nonempty frame tuple"),
    ],
)
def test_f1a_11_through_f1a_14_invalid_frame_collections_are_rejected(
    frames: object, message: str
) -> None:
    with pytest.raises(TypeError, match=message):
        ExperienceFrameSet(schema_version="1.0.0", frames=frames)


def test_f1a_15_subclassed_frame_is_rejected() -> None:
    class SubclassedFrame(ExperienceFrame):
        pass

    source = frame("experience-one")
    subclass = SubclassedFrame(
        schema_version=source.schema_version,
        policy_id=source.policy_id,
        policy_version=source.policy_version,
        source_ref=source.source_ref,
        source_digest=source.source_digest,
        source_status=source.source_status,
        experience_id=source.experience_id,
        version_id=source.version_id,
        predecessor_version_id=source.predecessor_version_id,
        experience_type=source.experience_type,
        content=source.content,
        provenance_refs=source.provenance_refs,
        created_at=source.created_at,
    )

    with pytest.raises(TypeError, match="exact ExperienceFrame"):
        frame_set(subclass)


def test_f1a_14_raw_dict_frame_is_rejected() -> None:
    with pytest.raises(TypeError, match="exact ExperienceFrame"):
        frame_set({"experience_id": "experience-one"})


def test_f1a_16_duplicate_source_ref_is_rejected() -> None:
    source = frame("experience-one")
    duplicate = replace(source, version_id="v2")

    with pytest.raises(TypeError, match="source refs must be unique"):
        frame_set(source, duplicate)


def test_f1a_17_wrong_schema_version_is_rejected() -> None:
    with pytest.raises(TypeError, match="schema version is unsupported"):
        ExperienceFrameSet(schema_version="0.0.0", frames=(frame("experience-one"),))


def test_f1a_18_carrier_mutation_is_rejected() -> None:
    carrier = frame_set(frame("experience-one"))

    with pytest.raises(FrozenInstanceError):
        carrier.schema_version = "2.0.0"
    with pytest.raises(FrozenInstanceError):
        carrier.frames = ()


def test_f1a_19_and_f1a_20_public_surface_is_bounded() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    class_node = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ExperienceFrameSet"
    )
    method_names = {
        node.name
        for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("__")
    }

    assert method_names == {"to_dict", "canonical_serialization", "digest"}
