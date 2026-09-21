from __future__ import annotations

from hashlib import sha256

from julia_core.identity import IdentityRef, IdentityStatus
from julia_core.memory_experience import (
    MemoryExperienceRef,
    MemoryExperienceStatus,
    MemoryExperienceType,
)
from julia_core.projection.contracts import (
    ExperienceFrame,
    ExperienceFrameSet,
    IdentityFrame,
    IdentityFrameSet,
)

from julia_core.context_admission import (
    CanonicalConversationProvenance,
    CanonicalConversationSource,
    CurrentConversationalTaskContext,
    ExclusiveAdmissionRequest,
)
from julia_core.context_admission.contracts import canonical_json
from julia_core.persona_self_binding import (
    AuthorityFamily,
    AuthorityReference,
    ExecutionSubstratePolicy,
    GovernanceEventType,
    GovernanceProvenanceEvent,
    IntegrityContract,
    PersonaSelfBinding,
    PersonaSelfBindingLifecycle,
    PersonaSelfBindingProjector,
    RelationshipAuthority,
    RelationshipAuthorityState,
    SupersessionContract,
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
        provenance_refs=(
            provenance_refs
            if provenance_refs is not None
            else ({"source_ref": "fixture://eng12a/identity", "source_digest": digest},)
        ),
    )


def canonical_identity_frame_set(
    *, identity: IdentityFrame | None = None
) -> IdentityFrameSet:
    return IdentityFrameSet(
        schema_version="1.0.0",
        frames=(identity or canonical_identity_frame(),),
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
        provenance_refs=(
            provenance_refs
            if provenance_refs is not None
            else (
                {"source_ref": "fixture://eng12a/experience", "source_digest": digest},
            )
        ),
        created_at="2026-09-12T00:00:00Z",
    )


def canonical_experience_frame_set() -> ExperienceFrameSet:
    return ExperienceFrameSet(
        schema_version="1.0.0",
        frames=(canonical_experience_frame(),),
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
        bounded_state=(
            {"surface": "terminal", "open_loop_count": 1}
            if bounded_state is None
            else bounded_state
        ),
        provenance=provenance
        or CanonicalConversationProvenance(
            source_type=CanonicalConversationSource.CONVERSATION_RUNTIME,
            source_ref="conversation_runtime://eng12a/current-task",
            source_digest="c" * 64,
            observed_at="2026-09-12T00:00:00Z",
        ),
    )


def canonical_request(
    *, identity=None, experiences=None, current_task=None
) -> ExclusiveAdmissionRequest:
    return ExclusiveAdmissionRequest(
        identity_frames=canonical_identity_frame_set(identity=identity),
        experience_frames=(
            experiences if experiences is not None else canonical_experience_frame_set()
        ),
        current_task_context=current_task or canonical_current_task_context(),
    )


def canonical_persona_self_binding(
    *,
    identity: IdentityFrameSet | None = None,
    experiences: ExperienceFrameSet | None = None,
):
    identity_frames = identity or canonical_identity_frame_set()
    experience_frames = experiences or canonical_experience_frame_set()

    def projected_digest(frame_set) -> str:
        return sha256(
            canonical_json(frame_set.model_visible_projection()).encode("utf-8")
        ).hexdigest()

    binding = PersonaSelfBinding(
        schema_version="julia_core.persona_self_binding.v1",
        binding_id="persona-binding-eng12a",
        persona_self_id="persona-self-eng12a",
        identity_authority=AuthorityReference(
            authority_type=AuthorityFamily.IDENTITY_FRAME_SET,
            authority_id="identity-frame-set-eng12a",
            source_digest=identity_frames.digest(),
            projected_digest=projected_digest(identity_frames),
        ),
        experience_authority=AuthorityReference(
            authority_type=AuthorityFamily.EXPERIENCE_FRAME_SET,
            authority_id="experience-frame-set-eng12a",
            source_digest=experience_frames.digest(),
            projected_digest=projected_digest(experience_frames),
        ),
        relationship_authority=RelationshipAuthority(
            RelationshipAuthorityState.ABSENT, None
        ),
        execution_substrate_policy=ExecutionSubstratePolicy(),
        binding_version="v1",
        predecessor_binding_id=None,
        predecessor_binding_version=None,
        lineage_id="persona-lineage-eng12a",
        lifecycle_status=PersonaSelfBindingLifecycle.ADMITTED_ACTIVE,
        supersession=SupersessionContract(None, None),
        governance_provenance=(
            GovernanceProvenanceEvent(
                event_id="admit-persona-binding",
                event_type=GovernanceEventType.ADMIT_AND_ACTIVATE,
                actor="owner-governance",
                reason="test fixture admission",
                occurred_at="2026-09-21T00:00:00Z",
            ),
        ),
        integrity=IntegrityContract("UTF8_JSON_SORTED_KEYS_COMPACT", "sha256"),
    )
    return binding, PersonaSelfBindingProjector.project(binding)
