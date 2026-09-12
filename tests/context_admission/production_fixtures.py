from __future__ import annotations

from julia_core.identity import IdentityRef, IdentityStatus
from julia_core.memory_experience import (
    MemoryExperienceRef,
    MemoryExperienceStatus,
    MemoryExperienceType,
)
from julia_core.projection.contracts import ExperienceFrame, IdentityFrame

from julia_core.context_admission import (
    CanonicalConversationProvenance,
    CanonicalConversationSource,
    CurrentConversationalTaskContext,
    ExclusiveAdmissionRequest,
)


def canonical_identity_frame(*, provenance_refs=None) -> IdentityFrame:
    digest = "a" * 64
    return IdentityFrame(
        schema_version="1.0.0",
        policy_id="persona_projection.identity_only",
        policy_version="1.0.0",
        source_ref=IdentityRef("identity-lineage-eng12a", "v1"),
        source_digest=digest,
        source_status=IdentityStatus.ADMITTED,
        identity_id="identity-eng12a",
        predecessor_version_id=None,
        anchors=({"anchor_id": "boundary", "statement": "Use governed context only"},),
        values=(),
        boundaries=({"boundary_id": "exclusive-gateway", "rule": "C03 only"},),
        relationship_role_anchors=(),
        provenance_refs=provenance_refs
        if provenance_refs is not None
        else ({"source_ref": "fixture://eng12a/identity", "source_digest": digest},),
    )


def canonical_experience_frame(*, provenance_refs=None) -> ExperienceFrame:
    digest = "b" * 64
    return ExperienceFrame(
        schema_version="1.0.0",
        policy_id="experience_projection.memory_experience_only",
        policy_version="1.0.0",
        source_ref=MemoryExperienceRef("experience-eng12a", "v1"),
        source_digest=digest,
        source_status=MemoryExperienceStatus.ADMITTED,
        experience_id="experience-eng12a",
        version_id="v1",
        predecessor_version_id=None,
        experience_type=MemoryExperienceType.PROJECT_COMMITMENT,
        content={"commitment": "Do not bypass governed context admission"},
        provenance_refs=provenance_refs
        if provenance_refs is not None
        else ({"source_ref": "fixture://eng12a/experience", "source_digest": digest},),
        created_at="2026-09-12T00:00:00Z",
    )


def canonical_current_task_context(
    *, bounded_state=None, provenance=None, turn_id="turn-eng12a-1"
) -> CurrentConversationalTaskContext:
    return CurrentConversationalTaskContext(
        schema_version="1.0.0",
        conversation_id="conversation-eng12a",
        turn_id=turn_id,
        task_intent="Implement C03 conformance",
        task_domain="software_engineering",
        current_modality="text",
        bounded_state={"surface": "terminal", "open_loop_count": 1}
        if bounded_state is None
        else bounded_state,
        provenance=provenance
        or CanonicalConversationProvenance(
            source_type=CanonicalConversationSource.CONVERSATION_RUNTIME,
            source_ref="conversation_runtime://eng12a/current-task",
            source_digest="c" * 64,
            observed_at="2026-09-12T00:00:00Z",
        ),
    )


def canonical_request(
    *, identity=None, experience=None, current_task=None
) -> ExclusiveAdmissionRequest:
    return ExclusiveAdmissionRequest(
        identity_frame=identity or canonical_identity_frame(),
        experience_frame=experience or canonical_experience_frame(),
        current_task_context=current_task or canonical_current_task_context(),
    )
