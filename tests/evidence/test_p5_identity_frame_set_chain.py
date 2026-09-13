from __future__ import annotations

import json
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import pytest

from tests.context_admission.production_fixtures import (
    canonical_current_task_context,
)

from julia_core.context_admission import (
    CurrentConversationalTaskContext,
    ExclusiveAdmissionGate,
    ExclusiveAdmissionRequest,
)
from julia_core.context_admission.semantic_binding import (
    ExactAdmittedSemanticBinder,
    SemanticBindingRequest,
)
from julia_core.execution_observer import (
    CanonicalExecutionObservationRejected,
    EvidenceOnlyCanonicalExecutionObserver,
    ProviderExecutionOutcome,
)
from julia_core.identity import (
    GovernedIdentity,
    IdentityRef,
    IdentityStatus,
)
from julia_core.memory_experience import (
    GovernedMemoryExperience,
    MemoryExperienceStatus,
)
from julia_core.projection.policy import (
    ExperienceProjectionPolicy,
    PersonaProjectionPolicy,
)
from julia_core.projection.contracts import (
    ExperienceFrameSet,
    IdentityFrameSet,
)
from julia_core.runtime.assistant_runtime import (
    JuliaAssistantRuntime,
    RuntimeTurnRequest,
)
from tools.mira_migration.admission_sim import construct_admission_inputs


REPOSITORY = Path(__file__).resolve().parents[2]
PREFLIGHT_PATH = REPOSITORY / "artifacts/continuity/P5_C_REAL_CANARY_PREFLIGHT_V1.json"
EVIDENCE_PATH = (
    REPOSITORY / "artifacts/continuity/P5_IDENTITY_FRAME_SET_CARDINALITY_FIX_V1.json"
)
CUE = "Hi Mira，还记得我吗？"

IDENTITIES = (
    (
        "mira-golden:mira-id-cand-001",
        "mira-id-cand-001-v0.1-preview",
        "identity://mira-golden%3Amira-id-cand-001/mira-id-cand-001-v0.1-preview",
        "7580e0a930dc7f3d5446da2cdd8d1c23cf251e12929fb2f3baa056bd9739dd44",
    ),
    (
        "mira-golden:mira-id-cand-002",
        "mira-id-cand-002-v0.1-preview",
        "identity://mira-golden%3Amira-id-cand-002/mira-id-cand-002-v0.1-preview",
        "adaa2508c4e475a700c394eb205e278d515dfe014ccdaa4bab3c3e7b7dcd5f3a",
    ),
    (
        "mira-golden:mira-id-cand-003",
        "mira-id-cand-003-v0.1-preview",
        "identity://mira-golden%3Amira-id-cand-003/mira-id-cand-003-v0.1-preview",
        "0008a5e157347ae9b0dd8600d661ec4a0e3fbd1858673cd04dc7c7b812a96c29",
    ),
)

EXPERIENCES = (
    (
        "golden-mira:GM-CMIR-001",
        "v0.2-preview",
        "4e29eb74de7f29bbf8d69485a7c18b5dceb06486d7e1d986d668a30c85fb7228",
    ),
    (
        "golden-mira:GM-CMIR-002",
        "v0.2-preview",
        "e4374452173b144ce48dbefa5299f1ac3dc15cec3615b8e7d528176293536f93",
    ),
    (
        "golden-mira:GM-CMIR-004",
        "v0.1-preview",
        "ba4edeff89bc8054be19d7a48226fcef74359bc85d17dbd6abea4b754b905f97",
    ),
    (
        "golden-mira:GM-CMIR-006",
        "v0.1-preview",
        "47636f46d2934eeb66f91c8202e2245c180b7077fddd04ca6445683308b54f2c",
    ),
    (
        "golden-mira:GM-CMIR-008",
        "v0.1-preview",
        "08c95873446b01949b7aec50ad35ebbe36ce8b5b9ad87aca45c51b627f70c408",
    ),
    (
        "golden-mira:GM-CMIR-011",
        "formation-draft-preview",
        "3107a3ab38d0fc0d2446752f48bedebf2ee336e3cb8b22811bf3c156247a4ae9",
    ),
    (
        "golden-mira:GM-CMIR-011",
        "frozen-final-preview",
        "3c31de4d62ecfd5d7857a5a4df85725affa0862d0055b5527d7d80f27fcc8ad8",
    ),
    (
        "golden-mira:GM-CMIR-013",
        "v0.2-preview",
        "8e2d16304357b7fb72b5b6cb53501be5d8743b3c687d2f0aadf3a9e1e132046c",
    ),
)


@lru_cache(maxsize=1)
def exact_reviewed_canonical_inputs():
    return construct_admission_inputs(REPOSITORY)


def golden_identity_frames() -> IdentityFrameSet:
    versions, _ = exact_reviewed_canonical_inputs()
    policy = PersonaProjectionPolicy()
    frames = [
        _with_canonical_binding(
            policy._project(
                GovernedIdentity(
                    version=version,
                    status=IdentityStatus.ADMITTED,
                    governance_events=(),
                )
            )
        )
        for version in versions
    ]
    return IdentityFrameSet(schema_version="1.0.0", frames=tuple(frames))


def golden_experience_frames() -> ExperienceFrameSet:
    _, candidates = exact_reviewed_canonical_inputs()
    policy = ExperienceProjectionPolicy()
    frames = [
        _with_canonical_binding(
            policy._project(
                GovernedMemoryExperience(
                    record=candidate.record,
                    status=MemoryExperienceStatus.ADMITTED,
                    governance_events=(),
                )
            )
        )
        for candidate in candidates
    ]
    return ExperienceFrameSet(schema_version="1.0.0", frames=tuple(frames))


def _with_canonical_binding(frame):
    binding = {
        "source_ref": frame.source_ref.uri,
        "source_digest": frame.source_digest,
    }
    return replace(frame, provenance_refs=(*frame.provenance_refs, binding))


def golden_current_task() -> CurrentConversationalTaskContext:
    return replace(canonical_current_task_context(), task_intent=CUE)


def require_golden_identities(identity_frames: IdentityFrameSet) -> None:
    expected_refs = tuple(IdentityRef(item[0], item[1]) for item in IDENTITIES)
    expected_digests = tuple(item[3] for item in IDENTITIES)
    if (
        identity_frames.ordered_source_refs() != expected_refs
        or tuple(item.source_digest for item in identity_frames.frames)
        != expected_digests
        or any(
            item.source_status is not IdentityStatus.ADMITTED
            for item in identity_frames.frames
        )
    ):
        raise ValueError("exact three Golden Mira identities are required in order")


def golden_chain(
    identity_frames: IdentityFrameSet | None = None,
) -> tuple:
    identities = identity_frames or golden_identity_frames()
    require_golden_identities(identities)
    experiences = golden_experience_frames()
    current_task = golden_current_task()
    admission = ExclusiveAdmissionRequest(
        identity_frames=identities,
        experience_frames=experiences,
        current_task_context=current_task,
    )
    package = ExclusiveAdmissionGate().seal(admission)
    binding = ExactAdmittedSemanticBinder().bind(
        SemanticBindingRequest(package, identities, experiences, current_task)
    )
    envelope = JuliaAssistantRuntime().prepare(
        RuntimeTurnRequest(binding=binding, provider_id="deepseek")
    )
    return identities, experiences, current_task, package, binding, envelope


def test_golden_vector_matches_accepted_preflight() -> None:
    preflight = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    identity_refs = preflight["canonical_input"]["identity_refs"]
    memory_refs = preflight["canonical_input"]["ordered_memory_experience_refs"]
    identities = golden_identity_frames()
    experiences = golden_experience_frames()

    assert tuple(item["ref"] for item in identity_refs) == tuple(
        item.source_ref.uri for item in identities.frames
    )
    assert tuple(item["digest"] for item in identity_refs) == tuple(
        item.source_digest for item in identities.frames
    )
    assert tuple(item["ref"] for item in memory_refs) == tuple(
        item.source_ref.uri for item in experiences.frames
    )
    assert tuple(item["digest"] for item in memory_refs) == tuple(
        item.source_digest for item in experiences.frames
    )


def test_evidence_digests_match_executed_golden_chain() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    identities, experiences, _, _, _, _ = golden_chain()

    assert evidence["golden_mira_vector"]["identity_set_digest"] == (
        identities.digest()
    )
    assert evidence["golden_mira_vector"]["experience_frame_set_digest"] == (
        experiences.digest()
    )
    assert [
        item["projected_frame_digest"]
        for item in evidence["golden_mira_vector"]["identities"]
    ] == list(identities.ordered_frame_digests())


def test_golden_three_identity_chain_is_exact_without_provider_call() -> None:
    identities, experiences, current_task, package, binding, envelope = golden_chain()

    assert package.identity_frame_count == 3
    assert package.identity_frame_digests == identities.ordered_frame_digests()
    assert package.identity_digest == identities.digest()
    assert binding.units[0].canonical_content == identities.canonical_serialization()
    assert [item.frame_name for item in binding.units][0] == "identity_frame_set"

    record = EvidenceOnlyCanonicalExecutionObserver().observe_outcome(
        identity_frames=identities,
        experience_frames=experiences,
        current_task_context=current_task,
        package=package,
        binding=binding,
        envelope=envelope,
        outcome=ProviderExecutionOutcome.not_run("P81_PREFLIGHT_NO_PROVIDER_CALL"),
    )
    provenance = record.provenance
    assert [item.source_ref["lineage_id"] for item in provenance.identity_frames] == [
        item[0] for item in IDENTITIES
    ]
    assert [item.source_digest for item in provenance.identity_frames] == [
        item[3] for item in IDENTITIES
    ]
    assert provenance.identity_frame_set_digest == identities.digest()
    assert provenance.ordered_identity_frame_digest_manifest == (
        identities.ordered_frame_digests()
    )
    assert [
        item.source_ref["experience_id"] for item in provenance.experience_frames
    ] == [item[0] for item in EXPERIENCES]
    assert record.execution.disposition == "NOT_RUN"


def test_missing_golden_identity_fails_closed_before_c03() -> None:
    partial = IdentityFrameSet(
        schema_version="1.0.0", frames=golden_identity_frames().frames[:2]
    )

    with pytest.raises(ValueError, match="exact three Golden Mira identities"):
        golden_chain(partial)


def test_wrong_golden_identity_digest_status_or_ref_fails_closed() -> None:
    identities = golden_identity_frames()
    wrong_digest = replace(identities.frames[1], source_digest="f" * 64)
    wrong_status = replace(identities.frames[1], source_status=IdentityStatus.CANDIDATE)
    wrong_ref = replace(
        identities.frames[1],
        source_ref=IdentityRef("identity://wrong", "wrong"),
        provenance_refs=(
            {"source_ref": "identity://wrong", "source_digest": "f" * 64},
        ),
    )

    for frame in (wrong_digest, wrong_status, wrong_ref):
        candidate = IdentityFrameSet(
            schema_version="1.0.0",
            frames=(identities.frames[0], frame, identities.frames[2]),
        )
        with pytest.raises(ValueError, match="exact three Golden Mira identities"):
            golden_chain(candidate)


def test_identity_reorder_is_detected_by_observer() -> None:
    identities, experiences, current_task, package, binding, envelope = golden_chain()
    frames = identities.frames
    reordered = IdentityFrameSet(
        schema_version="1.0.0", frames=(frames[1], frames[0], frames[2])
    )

    with pytest.raises(CanonicalExecutionObservationRejected):
        EvidenceOnlyCanonicalExecutionObserver().observe_outcome(
            identity_frames=reordered,
            experience_frames=experiences,
            current_task_context=current_task,
            package=package,
            binding=binding,
            envelope=envelope,
            outcome=ProviderExecutionOutcome.not_run("ORDER_MISMATCH"),
        )
