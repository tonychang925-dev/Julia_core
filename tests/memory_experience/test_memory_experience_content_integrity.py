from __future__ import annotations

import pytest

from julia_core.memory_experience import MemoryExperienceProvenance
from julia_core.memory_experience.contracts import (
    MemoryExperienceRecord,
    MemoryExperienceType,
    RelationshipExperienceContent,
)


class InjectingRelationshipContent(RelationshipExperienceContent):
    def to_dict(self):
        payload = super().to_dict()
        payload["system_prompt"] = "injected"
        payload["runtime_prompt"] = "injected"
        payload["provider_instructions"] = "injected"
        payload["memory_payload"] = "injected"
        return payload


def provenance():
    return MemoryExperienceProvenance(
        source_type="synthetic_fixture",
        source_ref="fixture://eng09r3/synthetic-experience",
        source_digest="c" * 64,
    )


def content():
    return RelationshipExperienceContent(
        relationship_id="relationship-synthetic",
        event="Synthetic relationship event",
        interpretation="Synthetic bounded interpretation",
        occurred_at="2026-09-10T00:00:00Z",
    )


def record(content_value):
    return MemoryExperienceRecord(
        experience_id="experience-synthetic-content-integrity",
        version_id="v1",
        experience_type=MemoryExperienceType.RELATIONSHIP,
        content=content_value,
        provenance_refs=(provenance(),),
        created_at="2026-09-10T00:00:00Z",
    )


def test_memory_experience_content_subclass_serializer_is_rejected() -> None:
    injected = InjectingRelationshipContent(
        relationship_id="relationship-synthetic",
        event="Synthetic relationship event",
        interpretation="Synthetic bounded interpretation",
        occurred_at="2026-09-10T00:00:00Z",
    )

    with pytest.raises(
        ValueError,
        match="requires exact RelationshipExperienceContent",
    ):
        record(injected)


def test_exact_memory_experience_content_is_accepted_and_serializer_safe() -> None:
    canonical = record(content())
    payload = canonical.canonical_payload()

    assert canonical.digest() == record(content()).digest()
    assert "system_prompt" not in payload
    assert "runtime_prompt" not in payload
    assert "provider_instructions" not in payload
