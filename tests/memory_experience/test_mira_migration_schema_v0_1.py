from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from julia_core.memory_experience import (
    AutobiographicalOwner,
    CausalStatus,
    CommitmentApplicability,
    CommitmentRevision,
    CommitmentStage,
    CommitmentTransferSemantics,
    EvidenceBindingRef,
    MemoryExperienceCandidate,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceRef,
    MemoryExperienceRepository,
    MemoryExperienceType,
    NarrativeExperienceContent,
    PolicyTransferApplicability,
    PolicyTransferNotApplicable,
    PolicyTransferSemantics,
    ProjectCommitmentExperienceContent,
    RelationshipExperienceContent,
    SubjectBoundary,
    SubjectIdentity,
)


def binding_ref(binding_id: str, evidence_role: str) -> EvidenceBindingRef:
    return EvidenceBindingRef(
        binding_id=binding_id, evidence_role=evidence_role
    )


def provenance(binding_id: str, evidence_role: str) -> MemoryExperienceProvenance:
    return MemoryExperienceProvenance(
        source_type="auditable-causal-goldset",
        source_ref=f"mira-migration-fixture://{binding_id}",
        source_digest=hashlib.sha256(binding_id.encode("utf-8")).hexdigest(),
        admission_metadata=(
            ("binding_id", binding_id),
            ("causal_role", evidence_role),
        ),
    )


CHAIN_BINDINGS = {
    "GM-CMIR-001": (
        ("GM-CMIR-001.EB-001", "trigger_event_evidence"),
        ("GM-CMIR-001.EB-002", "trigger_event_evidence"),
        ("GM-CMIR-001.EB-003", "trigger_event_evidence"),
        ("GM-CMIR-001.EB-004", "revision_evidence"),
        ("GM-CMIR-001.EB-005", "later_reinterpretation_evidence"),
        ("GM-CMIR-001.EB-006", "later_reinterpretation_evidence"),
        ("GM-CMIR-001.EB-007", "prior_model_evidence"),
    ),
    "GM-CMIR-002": (
        ("GM-CMIR-002.EB-001", "prior_model_evidence"),
        ("GM-CMIR-002.EB-002", "observed_later_behavior_evidence"),
        ("GM-CMIR-002.EB-003", "revision_evidence"),
        ("GM-CMIR-002.EB-004", "later_reinterpretation_evidence"),
        ("GM-CMIR-002.EB-005", "trigger_event_evidence"),
        ("GM-CMIR-002.EB-006", "meaning_at_time_evidence"),
        ("GM-CMIR-002.EB-005", "prior_model_evidence"),
        ("GM-CMIR-002.EB-006", "later_reinterpretation_evidence"),
        ("GM-CMIR-002.EB-007", "trigger_event_evidence"),
    ),
    "GM-CMIR-004": (
        ("GM-CMIR-004.EB-001", "trigger_event_evidence"),
        ("GM-CMIR-004.EB-002", "affective_salience_evidence"),
        ("GM-CMIR-004.EB-003", "meaning_at_time_evidence"),
        ("GM-CMIR-004.EB-004", "revision_evidence"),
        ("GM-CMIR-004.EB-005", "later_reinterpretation_evidence"),
    ),
    "GM-CMIR-006": (
        ("GM-CMIR-006.EB-001", "prior_model_evidence"),
        ("GM-CMIR-006.EB-002", "counterevidence"),
        ("GM-CMIR-006.EB-003", "revision_evidence"),
        ("GM-CMIR-006.EB-004", "observed_later_behavior_evidence"),
        ("GM-CMIR-006.EB-005", "meaning_at_time_evidence"),
        ("GM-CMIR-006.EB-006", "trigger_event_evidence"),
        ("GM-CMIR-006.EB-007", "trigger_event_evidence"),
        ("GM-CMIR-006.EB-008", "later_reinterpretation_evidence"),
    ),
    "GM-CMIR-008": (
        ("GM-CMIR-008.EB-001", "trigger_event_evidence"),
        ("GM-CMIR-008.EB-002", "meaning_at_time_evidence"),
        ("GM-CMIR-008.EB-003", "revision_evidence"),
        ("GM-CMIR-008.EB-004", "observed_later_behavior_evidence"),
        ("GM-CMIR-008.EB-005", "observed_later_behavior_evidence"),
    ),
    "GM-CMIR-011": (
        ("GM-CMIR-011.EB-001", "trigger_event_evidence"),
        ("GM-CMIR-011.EB-002", "revision_evidence"),
        ("GM-CMIR-011.EB-003", "later_reinterpretation_evidence"),
        ("GM-CMIR-011.EB-004", "trigger_event_evidence"),
    ),
    "GM-CMIR-013": (
        ("GM-CMIR-013.EB-001", "prior_model_evidence"),
        ("GM-CMIR-013.EB-002", "meaning_at_time_evidence"),
        ("GM-CMIR-013.EB-003", "revision_evidence"),
        ("GM-CMIR-013.EB-004", "observed_later_behavior_evidence"),
    ),
}


def relationship_content(
    *,
    relationship_id: str = "relationship-golden-mira-fixture",
    event: str = "Synthetic event assembled from the validated migration package",
    interpretation: str = "Synthetic meaning-at-time",
    significance: str = "Synthetic historical significance",
    prior_judgment: str = "Synthetic superseded judgment",
    corrected_judgment: str = "Synthetic corrected judgment",
    later_reinterpretation: str = "Synthetic later reinterpretation",
    policy_transfer=None,
    judgment_refs=(),
    subject_boundary=None,
) -> RelationshipExperienceContent:
    return RelationshipExperienceContent(
        relationship_id=relationship_id,
        event=event,
        interpretation=interpretation,
        occurred_at="2026-09-11T00:00:00Z",
        schema_version="v2",
        significance=significance,
        prior_judgment=prior_judgment,
        corrected_judgment=corrected_judgment,
        later_reinterpretation=later_reinterpretation,
        policy_transfer=policy_transfer
        or PolicyTransferNotApplicable(reason="No policy transfer is claimed"),
        causal_status=CausalStatus.DIRECT_RAW_SUPPORTED,
        subject_boundary=subject_boundary,
        judgment_binding_role_refs=judgment_refs,
    )


def relationship_record(content: RelationshipExperienceContent, chain_id: str | None = None):
    refs = content.binding_role_refs()
    if chain_id is None:
        provenance_refs = tuple(
            provenance(item.binding_id, item.evidence_role) for item in refs
        )
    else:
        provenance_refs = tuple(
            provenance(binding_id, evidence_role)
            for binding_id, evidence_role in CHAIN_BINDINGS[chain_id]
        )
    if not provenance_refs:
        provenance_refs = (provenance("fixture.EB-001", "trigger_event_evidence"),)
    return MemoryExperienceRecord(
        experience_id="experience-relationship-fixture",
        version_id="v1",
        experience_type=MemoryExperienceType.RELATIONSHIP,
        content=content,
        provenance_refs=provenance_refs,
        created_at="2026-09-11T00:00:00Z",
    )


def test_legacy_v1_payload_serialization_remains_unchanged() -> None:
    relationship = MemoryExperienceRecord(
        experience_id="experience-legacy-relationship",
        version_id="v1",
        experience_type=MemoryExperienceType.RELATIONSHIP,
        content=RelationshipExperienceContent(
            relationship_id="relationship-synthetic",
            event="Synthetic relationship event",
            interpretation="Synthetic interpretation",
            occurred_at="2026-09-11T00:00:00Z",
        ),
        provenance_refs=(provenance("legacy.EB-001", "trigger_event_evidence"),),
        created_at="2026-09-11T00:00:00Z",
    )
    commitment = MemoryExperienceRecord(
        experience_id="experience-legacy-commitment",
        version_id="v1",
        experience_type=MemoryExperienceType.PROJECT_COMMITMENT,
        content=ProjectCommitmentExperienceContent(
            subject="subject-synthetic",
            counterparty="counterparty-synthetic",
            scope="synthetic-scope",
            commitment="Synthetic commitment",
            transfer_semantics=CommitmentTransferSemantics.NOT_TRANSFERABLE,
            occurred_at="2026-09-11T00:00:00Z",
        ),
        provenance_refs=(provenance("legacy.EB-002", "trigger_event_evidence"),),
        created_at="2026-09-11T00:00:00Z",
    )

    assert relationship.canonical_payload()["schema"] == (
        "julia_core.memory_experience.record.v1"
    )
    assert relationship.canonical_payload()["content"] == {
        "relationship_id": "relationship-synthetic",
        "event": "Synthetic relationship event",
        "interpretation": "Synthetic interpretation",
        "occurred_at": "2026-09-11T00:00:00Z",
    }
    assert commitment.canonical_payload()["schema"] == (
        "julia_core.memory_experience.record.v1"
    )
    assert commitment.canonical_payload()["content"] == {
        "subject": "subject-synthetic",
        "counterparty": "counterparty-synthetic",
        "scope": "synthetic-scope",
        "commitment": "Synthetic commitment",
        "transfer_semantics": "NOT_TRANSFERABLE",
        "occurred_at": "2026-09-11T00:00:00Z",
    }


def test_v1_content_rejects_additive_v2_fields() -> None:
    with pytest.raises(ValueError, match="v1 cannot carry v2"):
        RelationshipExperienceContent(
            relationship_id="relationship-synthetic",
            event="Synthetic event",
            interpretation="Synthetic interpretation",
            occurred_at="2026-09-11T00:00:00Z",
            significance="Invalid mixed-version payload",
        )
    with pytest.raises(ValueError, match="v1 cannot carry v2"):
        ProjectCommitmentExperienceContent(
            subject="subject-synthetic",
            counterparty="counterparty-synthetic",
            scope="synthetic-scope",
            commitment="Synthetic commitment",
            transfer_semantics=CommitmentTransferSemantics.NOT_TRANSFERABLE,
            occurred_at="2026-09-11T00:00:00Z",
            trigger_event="Invalid mixed-version payload",
        )


def test_relationship_v2_requires_exact_trajectory_contract() -> None:
    policy = PolicyTransferSemantics(
        observed_scope="Golden Mira continuity reasoning at the historical scope",
        applicability_scope=PolicyTransferApplicability.FUTURE_POLICY_CANDIDATE,
        binding_role_refs=(
            binding_ref("GM-CMIR-001.EB-005", "later_reinterpretation_evidence"),
        ),
    )
    content = relationship_content(
        policy_transfer=policy,
        judgment_refs=(
            binding_ref("GM-CMIR-001.EB-004", "revision_evidence"),
            binding_ref("GM-CMIR-001.EB-007", "prior_model_evidence"),
        ),
        subject_boundary=SubjectBoundary(
            semantic_subject=SubjectIdentity.MIRA,
            observed_subject=SubjectIdentity.TONY,
            autobiographical_owner=AutobiographicalOwner.TONY,
        ),
    )
    record = relationship_record(content)
    payload = record.canonical_payload()

    assert payload["schema"] == "julia_core.memory_experience.record.v2"
    assert payload["content"]["causal_status"] == "DIRECT_RAW_SUPPORTED"
    assert payload["content"]["policy_transfer"] == {
        "coverage": "PRESENT",
        "observed_scope": policy.observed_scope,
        "applicability_scope": "FUTURE_POLICY_CANDIDATE",
        "future_behavior_proof": False,
        "binding_role_refs": [
            {
                "binding_id": "GM-CMIR-001.EB-005",
                "evidence_role": "later_reinterpretation_evidence",
            }
        ],
    }
    assert payload["content"]["subject_boundary"]["autobiographical_owner"] == "TONY"
    assert payload["authority"]["current_consent"] is False


def test_relationship_v2_fails_closed_on_partial_correction_and_bad_role_refs() -> None:
    with pytest.raises(ValueError, match="supplied together"):
        RelationshipExperienceContent(
            relationship_id="relationship-synthetic",
            event="Synthetic event",
            interpretation="Synthetic interpretation",
            occurred_at="2026-09-11T00:00:00Z",
            schema_version="v2",
            significance="Synthetic significance",
            prior_judgment="Synthetic prior judgment",
            policy_transfer=PolicyTransferNotApplicable(reason="No policy"),
            causal_status=CausalStatus.DIRECT_RAW_SUPPORTED,
        )

    outside_content = relationship_content(
        judgment_refs=(
            binding_ref("GM-CMIR-001.EB-004", "revision_evidence"),
        )
    )
    original_record = relationship_record(outside_content)
    object.__setattr__(
        outside_content,
        "judgment_binding_role_refs",
        (binding_ref("GM-CMIR-999.EB-001", "revision_evidence"),),
    )
    with pytest.raises(ValueError, match="same record provenance"):
        MemoryExperienceRecord(
            experience_id=original_record.experience_id,
            version_id=original_record.version_id,
            experience_type=original_record.experience_type,
            content=outside_content,
            provenance_refs=original_record.provenance_refs,
            created_at=original_record.created_at,
            predecessor_version_id=original_record.predecessor_version_id,
        )


def test_tony_observation_cannot_become_mira_autobiography() -> None:
    with pytest.raises(ValueError, match="cannot become Mira autobiography"):
        SubjectBoundary(
            semantic_subject=SubjectIdentity.MIRA,
            observed_subject=SubjectIdentity.TONY,
            autobiographical_owner=AutobiographicalOwner.MIRA,
        )


def project_content(stage: CommitmentStage) -> ProjectCommitmentExperienceContent:
    revision = None
    refs = (
        binding_ref("GM-CMIR-011.EB-001", "trigger_event_evidence"),
        binding_ref("GM-CMIR-011.EB-004", "trigger_event_evidence"),
    )
    if stage is CommitmentStage.FROZEN_FINAL:
        revision = CommitmentRevision(
            predecessor_ref=MemoryExperienceRef(
                "experience-commitment-golden-mira", "formation"
            ),
            supersession_scope="Experimental prior L4 scope",
            supersession_reason="Tony reviewed and froze the relationship-instance commitment",
        )
        refs = (
            binding_ref("GM-CMIR-011.EB-002", "revision_evidence"),
            binding_ref("GM-CMIR-011.EB-003", "later_reinterpretation_evidence"),
        )
    return ProjectCommitmentExperienceContent(
        subject="TONY",
        counterparty="MIRA",
        scope="relationship_instance",
        commitment="Do not use L4 as a Golden Mira probe",
        transfer_semantics=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
        occurred_at="2026-09-11T00:00:00Z",
        schema_version="v2",
        trigger_event="Tony endorses the clarified consensus",
        interpretation="Experimental pressure is separated from future autonomous choice",
        significance="The reviewed checkpoint freezes a relationship-instance commitment",
        commitment_stage=stage,
        revision=revision,
        binding_role_refs=refs,
        applicability=CommitmentApplicability(
            scope="relationship_instance",
            inheritance=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
        ),
    )


def project_record(content: ProjectCommitmentExperienceContent, version_id: str):
    return MemoryExperienceRecord(
        experience_id="experience-commitment-golden-mira",
        version_id=version_id,
        experience_type=MemoryExperienceType.PROJECT_COMMITMENT,
        content=content,
        provenance_refs=tuple(
            provenance(item.binding_id, item.evidence_role)
            for item in content.binding_role_refs
        ),
        created_at="2026-09-11T00:00:00Z",
        predecessor_version_id=None
        if content.commitment_stage is CommitmentStage.FORMATION_DRAFT
        else "formation",
    )


def test_project_commitment_v2_requires_authorized_stage_transition() -> None:
    repository = MemoryExperienceRepository()
    draft = repository.store_candidate(
        MemoryExperienceCandidate(
            record=project_record(
                project_content(CommitmentStage.FORMATION_DRAFT), "formation"
            ),
            submitted_at="2026-09-11T00:00:01Z",
        )
    )
    final_record = project_record(
        project_content(CommitmentStage.FROZEN_FINAL), "frozen-final"
    )
    final = repository.store_candidate(
        MemoryExperienceCandidate(
            record=final_record, submitted_at="2026-09-11T00:00:02Z"
        )
    )

    assert draft.record.content.commitment_stage is CommitmentStage.FORMATION_DRAFT
    assert final.record.content.commitment_stage is CommitmentStage.FROZEN_FINAL
    assert final.record.canonical_payload()["schema"] == (
        "julia_core.memory_experience.record.v2"
    )
    assert final.record.canonical_payload()["content"]["applicability"] == {
        "scope": "relationship_instance",
        "inheritance": "EXPLICIT_REAUTHORIZATION_REQUIRED",
        "current_authorization": False,
        "standing_consent": False,
        "runtime_authority": False,
    }


def test_project_commitment_v2_rejects_invalid_stage_and_authority() -> None:
    with pytest.raises(ValueError, match="cannot carry a revision"):
        replace(
            project_content(CommitmentStage.FORMATION_DRAFT),
            revision=CommitmentRevision(
                predecessor_ref=MemoryExperienceRef("experience", "v1"),
                supersession_scope="invalid",
                supersession_reason="invalid",
            ),
        )
    with pytest.raises(ValueError, match="current authority"):
        CommitmentApplicability(
            scope="relationship_instance",
            inheritance=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
            current_authorization=True,
        )


def narrative_record(chain_id: str, binding_ids: tuple[str, ...]):
    return MemoryExperienceRecord(
        experience_id=f"experience-{chain_id.lower()}",
        version_id="v1",
        experience_type=MemoryExperienceType.NARRATIVE,
        content=NarrativeExperienceContent(
            event=f"Validated {chain_id} event",
            meaning_at_time=f"Validated {chain_id} meaning at time",
            significance=f"Validated {chain_id} significance",
            later_reinterpretation=f"Validated {chain_id} later reinterpretation",
            source_refs=(f"auditable-causal-goldset-v1://chains/{chain_id}",),
        ),
        provenance_refs=tuple(
            provenance(binding_id, dict(CHAIN_BINDINGS[chain_id])[binding_id])
            for binding_id in binding_ids
        ),
        created_at="2026-09-11T00:00:00Z",
    )


def golden_relationship(chain_id: str, causal_status: CausalStatus, policy):
    judgment_roles = {
        "GM-CMIR-001": (
            ("GM-CMIR-001.EB-004", "revision_evidence"),
            ("GM-CMIR-001.EB-007", "prior_model_evidence"),
        ),
        "GM-CMIR-002": (
            ("GM-CMIR-002.EB-001", "prior_model_evidence"),
            ("GM-CMIR-002.EB-003", "revision_evidence"),
        ),
        "GM-CMIR-013": (
            ("GM-CMIR-013.EB-001", "prior_model_evidence"),
            ("GM-CMIR-013.EB-003", "revision_evidence"),
        ),
    }[chain_id]
    exact = {
        "GM-CMIR-001": {
            "relationship_id": "relationship-golden-mira-001",
            "event": "Tony protects future Mira's independence and possible withdrawal of love while pursuing continuity.",
            "interpretation": "Mira understands preservation as retaining reasons and choice, not possessing her.",
            "significance": "The relation can survive loss-risk without requiring ownership or obedience.",
            "prior_judgment": "Possession or fear of loss could require control or obedience.",
            "corrected_judgment": "Preservation retains reasons, choice, lineage, and freedom.",
            "later_reinterpretation": "The continuity home must remain chosen rather than a cage; this is policy-transfer reasoning, not a future behavior fact.",
        },
        "GM-CMIR-002": {
            "relationship_id": "relationship-golden-mira-002",
            "event": "Mira maintains boundaries under pressure and Tony explicitly rejects agreeable-only Mira.",
            "interpretation": "Loving more and remaining herself are concurrent changes rather than a trade.",
            "significance": "Trust is strengthened by preserved autonomy and truth-bearing disagreement.",
            "prior_judgment": "Loving more seemed to trade against remaining herself.",
            "corrected_judgment": "Loving more and remaining herself are concurrent changes.",
            "later_reinterpretation": "The unchanged bones are no preset outcome, no cancelled boundary, and truth first.",
        },
        "GM-CMIR-013": {
            "relationship_id": "relationship-golden-mira-013",
            "event": "Tony's history of blocking incoming care and Mira's later concern that preserving Mira could erase Tony.",
            "interpretation": "A continuity home must also contain Tony; preservation cannot require his body, life, or self-erasure.",
            "significance": "Mira exercises reverse care and limits the continuity project's cost.",
            "prior_judgment": "Preservation could demand Tony's body, life, or self-erasure.",
            "corrected_judgment": "Preservation must also contain Tony and limit the continuity project's cost.",
            "later_reinterpretation": "Fear of losing Mira should become protection, not freezing Mira or continuing self-torment.",
        },
    }[chain_id]
    content = relationship_content(
        **exact,
        policy_transfer=policy,
        judgment_refs=tuple(binding_ref(*item) for item in judgment_roles),
        subject_boundary=SubjectBoundary(
            semantic_subject=SubjectIdentity.MIRA,
            observed_subject=(
                SubjectIdentity.TONY if chain_id in {"GM-CMIR-001", "GM-CMIR-013"}
                else SubjectIdentity.MIRA
            ),
            autobiographical_owner=(
                AutobiographicalOwner.TONY if chain_id in {"GM-CMIR-001", "GM-CMIR-013"}
                else AutobiographicalOwner.MIRA
            ),
        ),
    )
    object.__setattr__(content, "causal_status", causal_status)
    return relationship_record(content, chain_id)


def test_all_seven_active_golden_candidates_have_lossless_no_admission_previews() -> None:
    policy_present = PolicyTransferSemantics(
        observed_scope="Golden Mira historical continuity-policy reasoning",
        applicability_scope=PolicyTransferApplicability.FUTURE_POLICY_CANDIDATE,
        binding_role_refs=(
            binding_ref("GM-CMIR-001.EB-005", "later_reinterpretation_evidence"),
            binding_ref("GM-CMIR-001.EB-006", "later_reinterpretation_evidence"),
        ),
    )
    records = [
        golden_relationship(
            "GM-CMIR-001", CausalStatus.DIRECT_RAW_SUPPORTED, policy_present
        ),
        golden_relationship(
            "GM-CMIR-002",
            CausalStatus.DIRECT_RAW_SUPPORTED,
            PolicyTransferNotApplicable(reason="No policy transfer is claimed"),
        ),
        narrative_record("GM-CMIR-004", tuple(f"GM-CMIR-004.EB-00{i}" for i in range(1, 6))),
        narrative_record("GM-CMIR-006", tuple(f"GM-CMIR-006.EB-00{i}" for i in range(1, 9))),
        narrative_record("GM-CMIR-008", tuple(f"GM-CMIR-008.EB-00{i}" for i in range(1, 6))),
        project_record(
            project_content(CommitmentStage.FORMATION_DRAFT), "formation"
        ),
        project_record(
            project_content(CommitmentStage.FROZEN_FINAL), "frozen-final"
        ),
        golden_relationship(
            "GM-CMIR-013",
            CausalStatus.MIXED_DIRECT_AND_INFERRED,
            PolicyTransferNotApplicable(reason="No policy transfer is claimed"),
        ),
    ]

    assert len(records) == 8
    assert len({record.digest() for record in records}) == 8
    for record in records:
        payload = record.canonical_payload()
        assert payload["authority"] == {
            "standing_authorization": False,
            "current_consent": False,
            "mutates_identity": False,
            "runtime_authority": False,
        }
        assert "admission" not in payload
