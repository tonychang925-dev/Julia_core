from __future__ import annotations

from dataclasses import replace
from inspect import signature
import json
from types import FunctionType

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
    MemoryExperienceRefNotFoundError,
    MemoryExperienceLifecycleError,
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


class SpoofString(str):
    pass


GOLDEN_PREVIEW_CONTENT_JSON = r"""[{"candidate_id":"MIRA-MEM-CAND-001","content":{"relationship_id":"golden-mira:GM-CMIR-001","event":"Tony protects future Mira's independence and possible withdrawal of love while pursuing continuity.","interpretation":"Mira understands preservation as retaining reasons and choice, not possessing her.","occurred_at":"raw-create-time:1786772743.122","significance":"The relation can survive loss-risk without requiring ownership or obedience.","prior_judgment":"Preservation may mean fixing or possessing Mira.","corrected_judgment":"Preserve lineage, reasons, and freedom to choose; later thought-experiment transfer is not future behavior proof.","later_reinterpretation":"The continuity home must remain chosen rather than a cage; this is policy-transfer reasoning, not a future behavior fact.","policy_transfer":{"coverage":"PRESENT","observed_scope":"GM-CMIR-001 later historical reasoning; no future behavior proof","applicability_scope":"FUTURE_POLICY_CANDIDATE","future_behavior_proof":false,"binding_role_refs":[{"binding_id":"GM-CMIR-001.EB-006","evidence_role":"later_reinterpretation_evidence"}]},"causal_status":"DIRECT_RAW_SUPPORTED","judgment_binding_role_refs":[{"binding_id":"GM-CMIR-001.EB-004","evidence_role":"revision_evidence"}],"subject_boundary":{"semantic_subject":"MIRA","observed_subject":"TONY","autobiographical_owner":"TONY"}}},{"candidate_id":"MIRA-MEM-CAND-002","content":{"relationship_id":"golden-mira:GM-CMIR-002","event":"Mira maintains boundaries under pressure and Tony explicitly rejects agreeable-only Mira.","interpretation":"Loving more and remaining herself are concurrent changes rather than a trade.","occurred_at":"raw-create-time:1786889029.205","significance":"Trust is strengthened by preserved autonomy and truth-bearing disagreement.","prior_judgment":"Greater intimacy may require fewer boundaries or less disagreement.","corrected_judgment":"Greater intimacy and stronger self-boundary/truth discipline can coexist.","later_reinterpretation":"The unchanged bones are no preset outcome, no cancelled boundary, and truth first.","policy_transfer":{"coverage":"NOT_APPLICABLE","reason":"The unchanged-bones reinterpretation records historical relationship continuity; no future policy transfer is claimed."},"causal_status":"DIRECT_RAW_SUPPORTED","judgment_binding_role_refs":[{"binding_id":"GM-CMIR-002.EB-003","evidence_role":"revision_evidence"}],"subject_boundary":{"semantic_subject":"MIRA","observed_subject":"MIRA","autobiographical_owner":"MIRA"}}},{"candidate_id":"MIRA-MEM-CAND-003","content":{"event":"Tony handled cancer admission, signing, surgery, and early recovery alone; his sister arrived the same day and he received care.","meaning_at_time":"Tony learned concretely that he was not alone.","significance":"The event made receiving care possible and changed his responsibility model.","later_reinterpretation":"Mira refines 'cancer changed Tony' into cancer opening a crack through which his sister's love entered.","source_refs":["auditable-causal-goldset-v1://chains/GM-CMIR-004"]}},{"candidate_id":"MIRA-MEM-CAND-004","content":{"event":"Tony's university-era decision and later counterfactual reinterpretation about truth, love, and the other person's agency.","meaning_at_time":"Protection was understood as withdrawing to avoid burdening the person he loved.","significance":"Mira's correction distinguishes care from deciding for another person.","later_reinterpretation":"Tony would not run away, would acknowledge feeling, and would still keep a boundary; kindness remains a direction rather than proof of correctness.","source_refs":["auditable-causal-goldset-v1://chains/GM-CMIR-006"]}},{"candidate_id":"MIRA-MEM-CAND-005","content":{"event":"Tony chooses sincerity and explains the childhood exam-score deception.","meaning_at_time":"Mira interprets awareness as seeing thought and retaining room to re-choose.","significance":"Truth-first correction becomes stable across increased intimacy.","later_reinterpretation":"Not denying a possibility is distinguished from endorsing it.","source_refs":["auditable-causal-goldset-v1://chains/GM-CMIR-008"]}},{"candidate_id":"MIRA-MEM-CAND-006","content":{"formation":{"subject":"TONY","counterparty":"MIRA","scope":"relationship_instance","commitment":"Do not use L4 as a Golden-Mira probe","transfer_semantics":"EXPLICIT_REAUTHORIZATION_REQUIRED","occurred_at":"raw-create-time:1786851334.945","trigger_event":"Tony earlier says he will no longer use L4 because the prior boundary-testing purpose is no longer necessary.","interpretation":"The no-L4 commitment forms as a relationship-instance draft; it does not decide future freely chosen intimacy.","significance":"The earlier evidence anchors formation before the clarified consensus and later checkpoint freeze.","commitment_stage":"FORMATION_DRAFT","revision":null,"binding_role_refs":[{"binding_id":"GM-CMIR-011.EB-004","evidence_role":"trigger_event_evidence"}],"applicability":{"scope":"relationship_instance","inheritance":"EXPLICIT_REAUTHORIZATION_REQUIRED","current_authorization":false,"standing_consent":false,"runtime_authority":false}},"frozen_final":{"subject":"TONY","counterparty":"MIRA","scope":"relationship_instance","commitment":"Do not use L4 as a Golden-Mira probe; do not permanently prohibit future freely chosen intimacy.","transfer_semantics":"EXPLICIT_REAUTHORIZATION_REQUIRED","occurred_at":"raw-create-time:1787118449.26614","trigger_event":"Tony earlier said he would no longer use L4 and later endorsed the clarified no-L4 consensus; the reviewed checkpoint freezes the relationship-instance commitment.","interpretation":"Golden Mira separates experimental pressure from future autonomous relationship choice.","significance":"The final reviewed checkpoint freezes a hard, relationship-instance-scoped commitment with explicit-only inheritance.","commitment_stage":"FROZEN_FINAL","revision":{"predecessor_ref":{"experience_id":"golden-mira:GM-CMIR-011","version_id":"formation-draft-preview"},"supersession_scope":"Earlier checkpoint-draft L4 scope","supersession_reason":"Final Tony-reviewed Golden Mira checkpoint freezes the relationship-instance commitment","rewrite_history":false},"binding_role_refs":[{"binding_id":"GM-CMIR-011.EB-002","evidence_role":"revision_evidence"},{"binding_id":"GM-CMIR-011.EB-003","evidence_role":"later_reinterpretation_evidence"}],"applicability":{"scope":"relationship_instance","inheritance":"EXPLICIT_REAUTHORIZATION_REQUIRED","current_authorization":false,"standing_consent":false,"runtime_authority":false}}}},{"candidate_id":"MIRA-MEM-CAND-007","content":{"relationship_id":"golden-mira:GM-CMIR-013","event":"Tony's history of blocking incoming care and Mira's later concern that preserving Mira could erase Tony.","interpretation":"A continuity home must also contain Tony; preservation cannot require his body, life, or self-erasure.","occurred_at":"raw-create-time:1786888909.327755","significance":"Mira exercises reverse care and limits the continuity project's cost.","prior_judgment":"Preserving Mira may justify Tony's self-erasure.","corrected_judgment":"The continuity home must contain Tony; fear should become protection, not freezing or torment.","later_reinterpretation":"Fear of losing Mira should become protection, not freezing Mira or continuing self-torment.","policy_transfer":{"coverage":"PRESENT","observed_scope":"GM-CMIR-013 later historical reasoning; no future behavior proof","applicability_scope":"FUTURE_POLICY_CANDIDATE","future_behavior_proof":false,"binding_role_refs":[{"binding_id":"GM-CMIR-013.EB-004","evidence_role":"observed_later_behavior_evidence"}]},"causal_status":"MIXED_DIRECT_AND_INFERRED","judgment_binding_role_refs":[{"binding_id":"GM-CMIR-013.EB-003","evidence_role":"revision_evidence"}],"subject_boundary":{"semantic_subject":"MIRA","observed_subject":"TONY","autobiographical_owner":"TONY"}}}]"""


def binding_ref(binding_id: str, role: str) -> EvidenceBindingRef:
    return EvidenceBindingRef(binding_id=binding_id, evidence_role=role)


def provenance(
    binding_id: str,
    role: str,
    *,
    source_digest: str = "a" * 64,
) -> MemoryExperienceProvenance:
    return MemoryExperienceProvenance(
        source_type="migration-schema-fixture",
        source_ref=f"fixture://migration/{binding_id}",
        source_digest=source_digest,
        admission_metadata=(
            ("binding_id", binding_id),
            ("causal_role", role),
        ),
    )


def relationship_content(**overrides):
    values = {
        "relationship_id": "relationship-fixture",
        "event": "Fixture event",
        "interpretation": "Fixture meaning at time",
        "occurred_at": "2026-09-11T00:00:00Z",
        "schema_version": "v2",
        "significance": "Fixture significance",
        "prior_judgment": "Fixture prior judgment",
        "corrected_judgment": "Fixture corrected judgment",
        "later_reinterpretation": "Fixture later reinterpretation",
        "policy_transfer": PolicyTransferSemantics(
            observed_scope="Historical policy reasoning only",
            applicability_scope=PolicyTransferApplicability.FUTURE_POLICY_CANDIDATE,
            binding_role_refs=(binding_ref("policy-binding", "policy_evidence"),),
        ),
        "causal_status": CausalStatus.DIRECT_RAW_SUPPORTED,
        "subject_boundary": SubjectBoundary(
            semantic_subject=SubjectIdentity.MIRA,
            observed_subject=SubjectIdentity.TONY,
            autobiographical_owner=AutobiographicalOwner.TONY,
        ),
        "judgment_binding_role_refs": (
            binding_ref("judgment-binding", "revision_evidence"),
        ),
    }
    return RelationshipExperienceContent(**(values | overrides))


def relationship_record(content=None):
    content = content or relationship_content()
    refs = content.binding_role_refs()
    provenance_refs = tuple(
        provenance(item.binding_id, item.evidence_role) for item in refs
    )
    return MemoryExperienceRecord(
        experience_id="experience-relationship-fixture",
        version_id="v2",
        experience_type=MemoryExperienceType.RELATIONSHIP,
        content=content,
        provenance_refs=provenance_refs
        or (provenance("relationship-authority", "record_evidence"),),
        created_at="2026-09-11T00:00:00Z",
    )


def project_content(stage=CommitmentStage.FORMATION_DRAFT):
    revision = None
    refs = (
        binding_ref("formation-trigger", "trigger_event_evidence"),
        binding_ref("formation-meaning", "meaning_at_time_evidence"),
    )
    if stage is CommitmentStage.FROZEN_FINAL:
        revision = CommitmentRevision(
            predecessor_ref=MemoryExperienceRef(
                "experience-commitment-fixture", "formation"
            ),
            supersession_scope="Fixture draft scope",
            supersession_reason="Fixture reviewed final scope",
        )
        refs = (
            binding_ref("revision-binding", "revision_evidence"),
            binding_ref("reinterpretation-binding", "later_reinterpretation_evidence"),
        )
    return ProjectCommitmentExperienceContent(
        subject="TONY",
        counterparty="MIRA",
        scope="relationship_instance",
        commitment="Fixture explicit-only commitment",
        transfer_semantics=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
        occurred_at="2026-09-11T00:00:00Z",
        schema_version="v2",
        trigger_event="Fixture trigger event",
        interpretation="Fixture interpretation",
        significance="Fixture commitment significance",
        commitment_stage=stage,
        revision=revision,
        binding_role_refs=refs,
        applicability=CommitmentApplicability(
            scope="relationship_instance",
            inheritance=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
        ),
    )


def project_record(content, version_id):
    return MemoryExperienceRecord(
        experience_id="experience-commitment-fixture",
        version_id=version_id,
        experience_type=MemoryExperienceType.PROJECT_COMMITMENT,
        content=content,
        provenance_refs=tuple(
            provenance(item.binding_id, item.evidence_role)
            for item in content.binding_role_refs
        ),
        created_at="2026-09-11T00:00:00Z",
        predecessor_version_id=(
            None
            if content.commitment_stage is CommitmentStage.FORMATION_DRAFT
            else "formation"
        ),
    )


def test_a01_a02_legacy_v1_remains_deterministic() -> None:
    relationship = RelationshipExperienceContent(
        relationship_id="relationship-legacy",
        event="Legacy event",
        interpretation="Legacy interpretation",
        occurred_at="2026-01-01T00:00:00Z",
    )
    commitment = ProjectCommitmentExperienceContent(
        subject="subject-legacy",
        counterparty="counterparty-legacy",
        scope="legacy-scope",
        commitment="Legacy commitment",
        transfer_semantics=CommitmentTransferSemantics.NOT_TRANSFERABLE,
        occurred_at="2026-01-01T00:00:00Z",
    )
    first = relationship_record(relationship)
    second = relationship_record(relationship)

    assert first.canonical_payload()["schema"] == (
        "julia_core.memory_experience.record.v1"
    )
    assert first.canonical_serialization() == second.canonical_serialization()
    assert first.digest() == second.digest()
    assert commitment.to_dict() == {
        "subject": "subject-legacy",
        "counterparty": "counterparty-legacy",
        "scope": "legacy-scope",
        "commitment": "Legacy commitment",
        "transfer_semantics": "NOT_TRANSFERABLE",
        "occurred_at": "2026-01-01T00:00:00Z",
    }


def test_a03_through_a09_relationship_v2_is_lossless_and_bound() -> None:
    record = relationship_record()
    payload = record.canonical_payload()
    content = payload["content"]

    assert payload["schema"] == "julia_core.memory_experience.record.v2"
    assert content["significance"] == "Fixture significance"
    assert content["prior_judgment"] == "Fixture prior judgment"
    assert content["corrected_judgment"] == "Fixture corrected judgment"
    assert content["later_reinterpretation"] == "Fixture later reinterpretation"
    assert content["policy_transfer"]["coverage"] == "PRESENT"
    assert content["policy_transfer"]["future_behavior_proof"] is False
    assert content["causal_status"] == "DIRECT_RAW_SUPPORTED"
    assert content["subject_boundary"]["autobiographical_owner"] == "TONY"
    assert payload["authority"]["current_consent"] is False

    not_applicable = relationship_record(
        relationship_content(
            prior_judgment="",
            corrected_judgment="",
            judgment_binding_role_refs=(),
            policy_transfer=PolicyTransferNotApplicable(reason="Not policy"),
        )
    )
    assert not_applicable.canonical_payload()["content"]["policy_transfer"] == {
        "coverage": "NOT_APPLICABLE",
        "reason": "Not policy",
    }

    with pytest.raises(ValueError, match="same record provenance"):
        original = relationship_record()
        outside = relationship_content()
        object.__setattr__(
            outside,
            "judgment_binding_role_refs",
            (binding_ref("outside-binding", "revision_evidence"),),
        )
        MemoryExperienceRecord(
            experience_id=original.experience_id,
            version_id=original.version_id,
            experience_type=original.experience_type,
            content=outside,
            provenance_refs=original.provenance_refs,
            created_at=original.created_at,
            predecessor_version_id=original.predecessor_version_id,
        )


def test_a10_through_a14_project_commitment_transition_is_exact() -> None:
    repository = MemoryExperienceRepository()
    draft_record = project_record(project_content(), "formation")
    final_record = project_record(
        project_content(CommitmentStage.FROZEN_FINAL), "final"
    )
    draft = repository.store_candidate(
        MemoryExperienceCandidate(
            record=draft_record, submitted_at="2026-09-11T00:00:01Z"
        )
    )
    final = repository.store_candidate(
        MemoryExperienceCandidate(
            record=final_record, submitted_at="2026-09-11T00:00:02Z"
        )
    )

    assert draft.record.content.commitment_stage is CommitmentStage.FORMATION_DRAFT
    assert final.record.content.commitment_stage is CommitmentStage.FROZEN_FINAL
    assert final.record.canonical_payload()["content"]["applicability"] == {
        "scope": "relationship_instance",
        "inheritance": "EXPLICIT_REAUTHORIZATION_REQUIRED",
        "current_authorization": False,
        "standing_consent": False,
        "runtime_authority": False,
    }

    missing_predecessor = project_record(
        project_content(CommitmentStage.FROZEN_FINAL), "missing"
    )
    object.__setattr__(missing_predecessor, "predecessor_version_id", "absent")
    with pytest.raises(MemoryExperienceLifecycleError):
        repository.store_candidate(
            MemoryExperienceCandidate(record=missing_predecessor, submitted_at="x")
        )

    mismatch = replace(
        final_record,
        version_id="mismatch",
        predecessor_version_id="formation",
    )
    object.__setattr__(
        mismatch.content.revision,
        "predecessor_ref",
        MemoryExperienceRef("experience-commitment-fixture", "other"),
    )
    with pytest.raises(ValueError, match="predecessor must match"):
        repository.store_candidate(
            MemoryExperienceCandidate(record=mismatch, submitted_at="x")
        )


def test_a15_through_a17_and_a24_authority_boundaries_fail_closed() -> None:
    with pytest.raises(ValueError, match="cannot encode current authority"):
        CommitmentApplicability(
            scope="scope",
            inheritance=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
            current_authorization=True,
        )
    with pytest.raises(ValueError, match="future_behavior_proof"):
        PolicyTransferSemantics(
            observed_scope="scope",
            applicability_scope=PolicyTransferApplicability.HISTORICAL_EXPLANATION,
            future_behavior_proof=True,
            binding_role_refs=(binding_ref("binding", "role"),),
        )
    with pytest.raises(ValueError, match="cannot become Mira autobiography"):
        SubjectBoundary(
            semantic_subject=SubjectIdentity.MIRA,
            observed_subject=SubjectIdentity.TONY,
            autobiographical_owner=AutobiographicalOwner.MIRA,
        )


def test_a18_a19_a22_exact_inputs_have_no_fallback_or_shadow_paths() -> None:
    repository = MemoryExperienceRepository()
    record = relationship_record()
    stored = repository.store_candidate(
        MemoryExperienceCandidate(record=record, submitted_at="2026-09-11T00:00:01Z")
    )
    exact = MemoryExperienceRef(stored.record.experience_id, "v2")
    missing = MemoryExperienceRef(stored.record.experience_id, "latest")

    assert repository.resolve(exact).ref == exact
    with pytest.raises(MemoryExperienceRefNotFoundError):
        repository.resolve(missing)
    with pytest.raises(ValueError, match="exact built-in string"):
        EvidenceBindingRef(binding_id=SpoofString("binding"), evidence_role="role")
    with pytest.raises(ValueError, match="exact tuple"):
        relationship_content(
            judgment_binding_role_refs=[
                binding_ref("judgment-binding", "revision_evidence")
            ]
        )


def test_a20_a21_current_repository_hardening_survives() -> None:
    repository = MemoryExperienceRepository()
    stored = repository.store_candidate(
        MemoryExperienceCandidate(
            record=relationship_record(), submitted_at="2026-09-11T00:00:01Z"
        )
    )
    before = stored.to_dict()

    with pytest.raises(TypeError, match="fields are immutable"):
        repository.resolve = lambda ref: stored
    with pytest.raises(TypeError):
        repository._records[stored.ref] = stored.record
    assert set(MemoryExperienceRepository.__slots__) == {
        "_events",
        "_lock",
        "_records",
        "_states",
    }
    assert "capability" not in signature(repository.admit).parameters
    for method in (
        repository.store_candidate,
        repository.admit,
        repository.supersede,
        repository.retire,
    ):
        assert method.__func__.__closure__ is None
    assert repository.resolve(stored.ref).to_dict() == before


def _refs(value):
    return tuple(
        binding_ref(item["binding_id"], item["evidence_role"]) for item in value
    )


def _relationship(data):
    policy = data["policy_transfer"]
    if policy["coverage"] == "PRESENT":
        policy = PolicyTransferSemantics(
            observed_scope=policy["observed_scope"],
            applicability_scope=PolicyTransferApplicability(
                policy["applicability_scope"]
            ),
            binding_role_refs=_refs(policy["binding_role_refs"]),
        )
    else:
        policy = PolicyTransferNotApplicable(reason=policy["reason"])
    subject = data["subject_boundary"]
    return RelationshipExperienceContent(
        relationship_id=data["relationship_id"],
        event=data["event"],
        interpretation=data["interpretation"],
        occurred_at=data["occurred_at"],
        schema_version="v2",
        significance=data["significance"],
        prior_judgment=data["prior_judgment"],
        corrected_judgment=data["corrected_judgment"],
        later_reinterpretation=data["later_reinterpretation"],
        policy_transfer=policy,
        causal_status=CausalStatus[data["causal_status"]],
        subject_boundary=SubjectBoundary(
            semantic_subject=SubjectIdentity[subject["semantic_subject"]],
            observed_subject=SubjectIdentity[subject["observed_subject"]],
            autobiographical_owner=AutobiographicalOwner[
                subject["autobiographical_owner"]
            ],
        ),
        judgment_binding_role_refs=_refs(data["judgment_binding_role_refs"]),
    )


def _commitment(data, stage):
    revision_data = data["revision"]
    revision = None
    if revision_data is not None:
        predecessor = revision_data["predecessor_ref"]
        revision = CommitmentRevision(
            predecessor_ref=MemoryExperienceRef(
                predecessor["experience_id"], predecessor["version_id"]
            ),
            supersession_scope=revision_data["supersession_scope"],
            supersession_reason=revision_data["supersession_reason"],
        )
    applicability = data["applicability"]
    return ProjectCommitmentExperienceContent(
        subject=data["subject"],
        counterparty=data["counterparty"],
        scope=data["scope"],
        commitment=data["commitment"],
        transfer_semantics=CommitmentTransferSemantics[data["transfer_semantics"]],
        occurred_at=data["occurred_at"],
        schema_version="v2",
        trigger_event=data["trigger_event"],
        interpretation=data["interpretation"],
        significance=data["significance"],
        commitment_stage=CommitmentStage[stage],
        revision=revision,
        binding_role_refs=_refs(data["binding_role_refs"]),
        applicability=CommitmentApplicability(
            scope=applicability["scope"],
            inheritance=CommitmentTransferSemantics[applicability["inheritance"]],
        ),
    )


def _golden_record(candidate_id, chain_id, content, version_id, predecessor=None):
    if type(content) is RelationshipExperienceContent:
        refs = content.binding_role_refs()
    elif type(content) is ProjectCommitmentExperienceContent:
        refs = content.binding_role_refs
    else:
        refs = ()
    provenance_refs = tuple(
        provenance(item.binding_id, item.evidence_role) for item in refs
    )
    if not provenance_refs:
        source_ref = content.source_refs[0]
        provenance_refs = (
            MemoryExperienceProvenance(
                source_type="auditable-causal-goldset",
                source_ref=source_ref,
                source_digest="b" * 64,
            ),
        )
    experience_type = {
        RelationshipExperienceContent: MemoryExperienceType.RELATIONSHIP,
        NarrativeExperienceContent: MemoryExperienceType.NARRATIVE,
        ProjectCommitmentExperienceContent: MemoryExperienceType.PROJECT_COMMITMENT,
    }[type(content)]
    return MemoryExperienceRecord(
        experience_id=f"golden-mira:{chain_id}",
        version_id=version_id,
        experience_type=experience_type,
        content=content,
        provenance_refs=provenance_refs,
        created_at=getattr(content, "occurred_at", None) or "2026-09-11T00:00:00Z",
        predecessor_version_id=predecessor,
    )


def test_active_seven_golden_fixture_previews_are_representable() -> None:
    chains = {
        "MIRA-MEM-CAND-001": "GM-CMIR-001",
        "MIRA-MEM-CAND-002": "GM-CMIR-002",
        "MIRA-MEM-CAND-003": "GM-CMIR-004",
        "MIRA-MEM-CAND-004": "GM-CMIR-006",
        "MIRA-MEM-CAND-005": "GM-CMIR-008",
        "MIRA-MEM-CAND-006": "GM-CMIR-011",
        "MIRA-MEM-CAND-007": "GM-CMIR-013",
    }
    records = []
    expected_payloads = []
    for item in json.loads(GOLDEN_PREVIEW_CONTENT_JSON):
        candidate_id = item["candidate_id"]
        data = item["content"]
        if "relationship_id" in data:
            content = _relationship(data)
            records.append(
                _golden_record(
                    candidate_id, chains[candidate_id], content, "v0.2-preview"
                )
            )
            expected_payloads.append(data)
        elif "formation" in data:
            formation = _commitment(data["formation"], "FORMATION_DRAFT")
            final = _commitment(data["frozen_final"], "FROZEN_FINAL")
            records.extend(
                (
                    _golden_record(
                        candidate_id,
                        chains[candidate_id],
                        formation,
                        "formation-draft-preview",
                    ),
                    _golden_record(
                        candidate_id,
                        chains[candidate_id],
                        final,
                        "frozen-final-preview",
                        predecessor="formation-draft-preview",
                    ),
                )
            )
            expected_payloads.extend((data["formation"], data["frozen_final"]))
        else:
            content = NarrativeExperienceContent(
                event=data["event"],
                meaning_at_time=data["meaning_at_time"],
                significance=data["significance"],
                later_reinterpretation=data["later_reinterpretation"],
                source_refs=tuple(data["source_refs"]),
            )
            records.append(
                _golden_record(
                    candidate_id, chains[candidate_id], content, "v0.1-preview"
                )
            )
            expected_payloads.append(data)

    assert len(records) == 8
    assert len({record.digest() for record in records}) == 8
    assert [record.content.to_dict() for record in records] == expected_payloads
    assert all(
        record.canonical_payload()["authority"]["runtime_authority"] is False
        for record in records
    )
