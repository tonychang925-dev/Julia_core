"""Deterministic Golden Mira candidate preview compiler.

The compiler constructs typed canonical-shaped previews in memory. It never
constructs repository candidates, stores records, admits semantics, hydrates
context, invokes providers, or generates persona text.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote

from julia_core.identity.contracts import (
    IdentityBoundary,
    IdentityContract,
    IdentityProvenance,
    IdentityValue,
    IdentityVersion,
)
from julia_core.memory_experience.contracts import (
    AutobiographicalOwner,
    CausalStatus,
    CommitmentApplicability,
    CommitmentRevision,
    CommitmentStage,
    CommitmentTransferSemantics,
    EvidenceBindingRef,
    MemoryExperienceProvenance,
    MemoryExperienceRecord,
    MemoryExperienceRef,
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


TASK_ID = "MIG-PREVIEW-REWORK-V0.1"
AGENT_ID = "agent-c"
CONTENT_REVIEW_SHA = "f9c7165f7275636e0dfbb7bc7f6268970001bcfb"
MIGRATION_PREP_SHA = "d3c9f76dc073199b0e05df6c0cf6a42b807c04fd"
MIGRATION_DRYRUN_SHA = "ecf34771d509168ce279ff7ff0289fbe2e97052f"
REVIEWED_SCHEMA_SHA = "1a630c2ac8809c5b064991dfcd87bebcd07d58ac"
PACKAGE_SHA256 = "be62e80d656c449348bdbb631e2525da8a63f3cd3814ee8aa5cdd6f4fbf87b7a"
LEDGER_SHA256 = "8c4d886fe81dc76ed998caf705ac590567891c41014dcbe72b9eedcbccd6c3b3"
DRYRUN_ARTIFACT_SHA256 = "71718bbb3097d0176bb05d80be92b50c09cc45a9dcd688eab57357240d7070c9"
DRYRUN_RESULT_DIGEST = "1d80db53ed6149e646162b1632f9542c926e1c86caa29a2f00c56b0ee7b92a8d"
SCHEMA_RESULT_SHA256 = "4bc169215fbce350dae1bd1502724c285233bf00f122a393a0b22316bc4ad8d9"
GOLDSET_SHA256 = "8234045ba1b2f08e182f57279bffafa3e4e910ecd0e21287c3d2dc5c02bc63fc"
RAW_SHA256 = "564ef9b1aa5457b56751f550d80b0eaa24e144f8d08bd2f6b8c0ff870b8e9420"
UNBOUND_RECORDS = frozenset(
    {"GM-CMIR-003", "GM-CMIR-005", "GM-CMIR-007", "GM-CMIR-009", "GM-CMIR-010", "GM-CMIR-012"}
)
ACTIVE_CHAINS = frozenset(
    {"GM-CMIR-001", "GM-CMIR-002", "GM-CMIR-004", "GM-CMIR-006", "GM-CMIR-008", "GM-CMIR-011", "GM-CMIR-013"}
)
FORBIDDEN_AUTHORITY_FLAGS = (
    "canonical_admission",
    "schema_mutation",
    "runtime_wiring",
    "context_admission",
    "provider_wiring",
    "production_cutover",
)
CANONICAL_SCHEMA_PATHS = (
    "julia_core/identity/contracts.py",
    "julia_core/identity/repository.py",
    "julia_core/identity/__init__.py",
    "julia_core/memory_experience/contracts.py",
    "julia_core/memory_experience/repository.py",
    "julia_core/memory_experience/__init__.py",
)


class MigrationCompilerError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if type(value) is not dict:
        raise MigrationCompilerError(f"{path} must contain a JSON object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_digest(value: Any) -> str:
    serialized = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _require(condition: bool, message: str) -> None:
    if condition is not True:
        raise MigrationCompilerError(message)


def verify_repository_binding(repository: Path, schema_sha: str) -> None:
    _require(schema_sha == REVIEWED_SCHEMA_SHA, "schema SHA is not the reviewed exact SHA")
    repository = repository.resolve()

    def git(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        )

    resolved = git("rev-parse", f"{schema_sha}^{{commit}}").stdout.strip()
    _require(resolved == schema_sha, "schema SHA does not resolve exactly")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", schema_sha, "HEAD"],
        cwd=repository,
        capture_output=True,
        text=True,
    )
    _require(ancestry.returncode == 0, "compiler HEAD does not descend from reviewed schema SHA")
    diff = subprocess.run(
        ["git", "diff", "--exit-code", schema_sha, "--", *CANONICAL_SCHEMA_PATHS],
        cwd=repository,
        capture_output=True,
        text=True,
    )
    _require(diff.returncode == 0, "reviewed canonical schema files were modified after the bound SHA")


def _verify_inputs(
    package_path: Path,
    ledger_path: Path,
    dryrun_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    package_digest = _sha256_file(package_path)
    ledger_digest = _sha256_file(ledger_path)
    dryrun_digest = _sha256_file(dryrun_path)
    _require(package_digest == PACKAGE_SHA256, "migration package hash mismatch")
    _require(ledger_digest == LEDGER_SHA256, "evidence ledger hash mismatch")
    _require(dryrun_digest == DRYRUN_ARTIFACT_SHA256, "dry-run artifact hash mismatch")

    package = _load_json(package_path)
    ledger = _load_json(ledger_path)
    dryrun = _load_json(dryrun_path)
    _require(package.get("artifact_id") == "MIRA_MIGRATION_PREP_PACKAGE_V1", "wrong package artifact")
    _require(
        package.get("base_sha") == "03460b191eac37c53dbbb2201beb6029e3ef288f",
        "package binding base SHA mismatch",
    )
    _require(package.get("status") == "PREP_COMPLETE_NO_ADMISSION", "package is not prep-complete")
    _require(ledger.get("ledger_id") == "MIRA_MIGRATION_EVIDENCE_LEDGER_V1", "wrong evidence ledger")
    _require(ledger.get("status") == "EXACT_RAW_VERIFIED_PREP_ONLY", "evidence ledger is not verified prep-only")
    _require(dryrun.get("artifact_id") == "MIRA_MIGRATION_DRY_RUN_RESULT_V1", "wrong dry-run artifact")
    _require(dryrun.get("migration_prep_sha") == MIGRATION_PREP_SHA, "dry-run prep SHA mismatch")
    _require(dryrun.get("status") == "PREP_VALIDATED_NO_ADMISSION", "dry run did not pass")
    _require(dryrun.get("result_digest") == DRYRUN_RESULT_DIGEST, "dry-run semantic digest mismatch")

    source_inventory = {
        item.get("source_id"): item for item in package.get("source_inventory", [])
    }
    _require(
        source_inventory.get("AUDITABLE_CAUSAL_GOLDSET_V1", {}).get("sha256") == GOLDSET_SHA256,
        "goldset hash mismatch in package",
    )
    _require(
        source_inventory.get("MIRA_GOLDEN_CHATGPT_HI_MIRA_CANDIDATE.json", {}).get("sha256") == RAW_SHA256,
        "RAW hash mismatch in package",
    )
    ledger_sources = ledger.get("source_artifacts", {})
    _require(ledger_sources.get("goldset", {}).get("sha256") == GOLDSET_SHA256, "ledger goldset hash mismatch")
    _require(ledger_sources.get("raw_export", {}).get("sha256") == RAW_SHA256, "ledger RAW hash mismatch")
    _require(ledger_sources.get("package", {}).get("sha256") == PACKAGE_SHA256, "ledger package hash mismatch")
    dryrun_inputs = dryrun.get("inputs", {})
    _require(dryrun_inputs.get("migration_package", {}).get("sha256") == PACKAGE_SHA256, "dry-run package hash mismatch")
    _require(dryrun_inputs.get("published_evidence_ledger", {}).get("sha256") == LEDGER_SHA256, "dry-run ledger hash mismatch")
    _require(dryrun_inputs.get("causal_goldset", {}).get("sha256") == GOLDSET_SHA256, "dry-run goldset hash mismatch")
    _require(dryrun_inputs.get("exact_raw_export", {}).get("sha256") == RAW_SHA256, "dry-run RAW hash mismatch")

    bindings = ledger.get("bindings", [])
    _require(len(bindings) == 42, "evidence ledger must contain exactly 42 assertions")
    _require(len({row.get("binding_id") for row in bindings}) == 40, "evidence ledger unique binding count mismatch")
    _require(
        all(row.get("evidence_grade") == "RAW_DIRECT" for row in bindings),
        "every ledger assertion must be exact RAW_DIRECT evidence",
    )
    raw_verification = dryrun.get("validations", {}).get("raw_assertions", {})
    _require(raw_verification.get("total") == 42, "dry-run RAW assertion total mismatch")
    _require(raw_verification.get("verified") == 42, "dry-run did not verify all RAW assertions")
    _require(raw_verification.get("failed") == 0, "dry-run RAW failure count is nonzero")
    _require(raw_verification.get("unique_binding_ids") == 40, "dry-run unique binding count mismatch")
    _require(raw_verification.get("method") == "direct RAW recomputation, not prior-result copy", "dry-run method mismatch")

    authority = package.get("authority", {})
    _require(all(authority.get(flag) is False for flag in FORBIDDEN_AUTHORITY_FLAGS), "package authority is not fail-closed")
    _require(all(item.get("blocked") is True for item in package.get("forbidden_upgrades", [])), "forbidden upgrade is not blocked")
    _require(len(package.get("identity_candidates", [])) == 3, "expected exactly three Identity candidates")
    _require(len(package.get("memory_experience_candidates", [])) == 7, "expected exactly seven Memory candidates")
    deferred_records = {
        item.get("record_id")
        for item in package.get("deferred_schema_gaps", [])
        if item.get("record_id")
    }
    _require(deferred_records == set(UNBOUND_RECORDS), "unbound CMIR quarantine set mismatch")
    active_chains = {item.get("chain_id") for item in package.get("memory_experience_candidates", [])}
    active_chains |= {item.get("chain_id") for item in package.get("identity_candidates", [])}
    _require(not deferred_records.intersection(active_chains), "unbound CMIR record entered active set")
    _require(active_chains == set(ACTIVE_CHAINS), "active chain set mismatch")
    _require(
        all(item.get("dry_run_validation") == "PASS" for item in dryrun.get("candidate_results", [])),
        "dry-run candidate failure cannot compile",
    )
    return package, ledger, dryrun


def _rows_by_binding(ledger: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for row in ledger["bindings"]:
        key = (row["binding_id"], row["causal_role"])
        if key in rows:
            raise MigrationCompilerError(f"duplicate provenance assertion {key}")
        rows[key] = row
    return rows


def _rows_for_chain(ledger: dict[str, Any], chain_id: str) -> list[dict[str, Any]]:
    rows = [row for row in ledger["bindings"] if row["chain_id"] == chain_id]
    if not rows:
        raise MigrationCompilerError(f"no evidence bindings for {chain_id}")
    return rows


def _time(rows: list[dict[str, Any]], binding_id: str, causal_role: str) -> str:
    for row in rows:
        if row["binding_id"] == binding_id and row["causal_role"] == causal_role:
            return f"raw-create-time:{row['create_time']}"
    raise MigrationCompilerError(f"missing time anchor {binding_id}/{causal_role}")


def _source_ref(row: dict[str, Any]) -> str:
    binding_id = quote(row["binding_id"], safe="")
    causal_role = quote(row["causal_role"], safe="")
    return f"auditable-causal-goldset-v1://assertions/{binding_id}/{causal_role}"


def _identity_provenance(rows: list[dict[str, Any]]) -> tuple[IdentityProvenance, ...]:
    return tuple(
        IdentityProvenance(
            source_type="auditable-causal-goldset",
            source_ref=_source_ref(row),
            source_digest=GOLDSET_SHA256,
            admission_metadata=(
                ("binding_id", row["binding_id"]),
                ("causal_role", row["causal_role"]),
                ("message_id", row["message_id"]),
            ),
        )
        for row in rows
    )


def _identity_preview(candidate: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    chain_id = candidate["chain_id"]
    rows = _rows_for_chain(ledger, chain_id)
    candidate_id = candidate["candidate_id"]
    semantic_key = "constraint" if candidate["identity_target"] == "IdentityBoundary" else "statement"
    field_name = "boundary" if semantic_key == "constraint" else "value"
    item_id = f"{candidate_id.lower()}-{field_name}"
    if candidate["identity_target"] == "IdentityBoundary":
        semantic_item = IdentityBoundary(boundary_id=item_id, constraint=candidate["statement"])
        boundaries: tuple[IdentityBoundary, ...] = (semantic_item,)
        values: tuple[IdentityValue, ...] = ()
    else:
        values = (IdentityValue(value_id=item_id, statement=candidate["statement"]),)
        boundaries = ()
    contract = IdentityContract(
        identity_id=candidate_id.lower(),
        anchors=(),
        values=values,
        boundaries=boundaries,
        relationship_role_anchors=(),
    )
    anchor = rows[0]
    version = IdentityVersion(
        contract=contract,
        lineage_id=f"mira-golden:{candidate_id.lower()}",
        version_id=f"{candidate_id.lower()}-v0.1-preview",
        predecessor_version_id=None,
        created_at=_time(rows, anchor["binding_id"], anchor["causal_role"]),
        provenance_refs=_identity_provenance(rows),
    )
    payload = version.canonical_payload()
    if "Tony" in payload["identity"] and candidate["identity_target"].startswith("Identity"):
        payload_identity = json.dumps(payload["identity"], ensure_ascii=False)
        if "Tony's" in payload_identity and "Mira" not in candidate["statement"]:
            raise MigrationCompilerError("Tony autobiography cannot compile as Mira Identity")
    return {
        "candidate_id": candidate_id,
        "chain_id": chain_id,
        "candidate_class": candidate["identity_target"],
        "compilation_state": "MAPPED_TYPED_PREVIEW_ONLY",
        "canonical_preview": {
            "type": "IdentityVersion",
            "payload": payload,
            "digest": version.digest(),
        },
        "exact_binding_coverage": {
            "assertions": len(rows),
            "unique_binding_ids": len({row["binding_id"] for row in rows}),
            "status": "PASS",
        },
        "subject_boundary": "MIRA_SEMANTIC_SUBJECT",
        "authority": {
            "repository_calls": 0,
            "admission_calls": 0,
            "runtime_calls": 0,
            "standing_authorization": False,
            "current_consent": False,
        },
        "blockers": ["CONTENT_REVIEW_PENDING", "ADMISSION_AUTHORITY_NONE"],
    }


def _memory_provenance(rows: list[dict[str, Any]]) -> tuple[MemoryExperienceProvenance, ...]:
    return tuple(
        MemoryExperienceProvenance(
            source_type="auditable-causal-goldset",
            source_ref=_source_ref(row),
            source_digest=GOLDSET_SHA256,
            admission_metadata=(
                ("binding_id", row["binding_id"]),
                ("causal_role", row["causal_role"]),
                ("message_id", row["message_id"]),
            ),
        )
        for row in rows
    )


def _record_preview(record: MemoryExperienceRecord, candidate: dict[str, Any], rows: list[dict[str, Any]], mapping: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "chain_id": candidate["chain_id"],
        "candidate_class": candidate["classification"],
        "compilation_state": "MAPPED_TYPED_PREVIEW_ONLY",
        "semantic_mapping": mapping,
        "canonical_preview": {
            "type": "MemoryExperienceRecord",
            "payload": record.canonical_payload(),
            "digest": record.digest(),
        },
        "exact_binding_coverage": {
            "assertions": len(rows),
            "unique_binding_ids": len({row["binding_id"] for row in rows}),
            "status": "PASS",
        },
        "authority": {
            "repository_calls": 0,
            "admission_calls": 0,
            "runtime_calls": 0,
            "standing_authorization": False,
            "current_consent": False,
            "runtime_authority": False,
        },
        "blockers": ["CONTENT_REVIEW_PENDING", "ADMISSION_AUTHORITY_NONE"],
    }


def _relationship_preview(candidate: dict[str, Any], ledger: dict[str, Any], corrected: dict[str, str]) -> dict[str, Any]:
    chain_id = candidate["chain_id"]
    rows = _rows_for_chain(ledger, chain_id)
    row_map = _rows_by_binding(ledger)
    revision_ref = {
        "GM-CMIR-001": ("GM-CMIR-001.EB-004", "revision_evidence"),
        "GM-CMIR-002": ("GM-CMIR-002.EB-003", "revision_evidence"),
        "GM-CMIR-013": ("GM-CMIR-013.EB-003", "revision_evidence"),
    }[chain_id]
    policy_ref = {
        "GM-CMIR-001": ("GM-CMIR-001.EB-006", "later_reinterpretation_evidence"),
        "GM-CMIR-002": ("GM-CMIR-002.EB-004", "later_reinterpretation_evidence"),
        "GM-CMIR-013": ("GM-CMIR-013.EB-004", "observed_later_behavior_evidence"),
    }[chain_id]
    event_ref = {
        "GM-CMIR-001": ("GM-CMIR-001.EB-001", "trigger_event_evidence"),
        "GM-CMIR-002": ("GM-CMIR-002.EB-005", "trigger_event_evidence"),
        "GM-CMIR-013": ("GM-CMIR-013.EB-003", "revision_evidence"),
    }[chain_id]
    causal_status = {
        "GM-CMIR-001": CausalStatus.DIRECT_RAW_SUPPORTED,
        "GM-CMIR-002": CausalStatus.DIRECT_RAW_SUPPORTED,
        "GM-CMIR-013": CausalStatus.MIXED_DIRECT_AND_INFERRED,
    }[chain_id]
    subject_boundary = SubjectBoundary(
        semantic_subject=SubjectIdentity.MIRA,
        observed_subject=SubjectIdentity.TONY
        if chain_id in {"GM-CMIR-001", "GM-CMIR-013"}
        else SubjectIdentity.MIRA,
        autobiographical_owner=AutobiographicalOwner.TONY
        if chain_id in {"GM-CMIR-001", "GM-CMIR-013"}
        else AutobiographicalOwner.MIRA,
    )
    policy_transfer = (
        PolicyTransferNotApplicable(
            reason=(
                "The unchanged-bones reinterpretation records historical relationship "
                "continuity; no future policy transfer is claimed."
            )
        )
        if chain_id == "GM-CMIR-002"
        else PolicyTransferSemantics(
            observed_scope=f"{chain_id} later historical reasoning; no future behavior proof",
            applicability_scope=PolicyTransferApplicability.FUTURE_POLICY_CANDIDATE,
            future_behavior_proof=False,
            binding_role_refs=(EvidenceBindingRef(*policy_ref),),
        )
    )
    content = RelationshipExperienceContent(
        relationship_id=f"golden-mira:{chain_id}",
        event=candidate["event"],
        interpretation=candidate["interpretation"],
        occurred_at=_time(rows, *event_ref),
        schema_version="v2",
        significance=candidate["significance"],
        prior_judgment=corrected["prior"],
        corrected_judgment=corrected["corrected"],
        later_reinterpretation=candidate["later_reinterpretation"],
        policy_transfer=policy_transfer,
        causal_status=causal_status,
        subject_boundary=subject_boundary,
        judgment_binding_role_refs=(EvidenceBindingRef(*revision_ref),),
    )
    record = MemoryExperienceRecord(
        experience_id=f"golden-mira:{chain_id}",
        version_id="v0.2-preview",
        experience_type=MemoryExperienceType.RELATIONSHIP,
        content=content,
        provenance_refs=_memory_provenance(rows),
        created_at=_time(rows, *revision_ref),
        predecessor_version_id=None,
    )
    _require(
        bool(row_map[revision_ref]["text_sha256"] and row_map[policy_ref]["text_sha256"]),
        "policy provenance tampering",
    )
    return _record_preview(record, candidate, rows, "RELATIONSHIP_V2_LOSSLESS")


def _narrative_preview(candidate: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    chain_id = candidate["chain_id"]
    rows = _rows_for_chain(ledger, chain_id)
    content = NarrativeExperienceContent(
        event=candidate["event"],
        meaning_at_time=candidate["meaning_at_time"],
        significance=candidate["significance"],
        later_reinterpretation=candidate["later_reinterpretation"],
        source_refs=(f"auditable-causal-goldset-v1://chains/{chain_id}",),
    )
    record = MemoryExperienceRecord(
        experience_id=f"golden-mira:{chain_id}",
        version_id="v0.1-preview",
        experience_type=MemoryExperienceType.NARRATIVE,
        content=content,
        provenance_refs=_memory_provenance(rows),
        created_at=_time(rows, rows[0]["binding_id"], rows[0]["causal_role"]),
        predecessor_version_id=None,
    )
    preview = _record_preview(record, candidate, rows, "NARRATIVE_V1_FROZEN_NARROW")
    preview["subject_boundary"] = candidate.get("subject_boundary", "MIRA_SEMANTIC_SUBJECT")
    preview["causal_provenance_projection"] = {
        "why_it_mattered": candidate["significance"],
        "later_reinterpretation": candidate["later_reinterpretation"],
        "authority": "NON_CANONICAL_COMPILER_PROVENANCE_PREVIEW",
    }
    return preview


def _project_preview(candidate: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    chain_id = candidate["chain_id"]
    rows = _rows_for_chain(ledger, chain_id)
    row_map = _rows_by_binding(ledger)
    formation_ref = ("GM-CMIR-011.EB-004", "trigger_event_evidence")
    revision_ref = ("GM-CMIR-011.EB-002", "revision_evidence")
    freeze_ref = ("GM-CMIR-011.EB-003", "later_reinterpretation_evidence")
    trigger_ref = ("GM-CMIR-011.EB-001", "trigger_event_evidence")
    formation_time = _time(rows, *formation_ref)
    revision_time = _time(rows, *revision_ref)
    _require(
        row_map[formation_ref]["create_time"]
        < min(
            row_map[freeze_ref]["create_time"],
            row_map[trigger_ref]["create_time"],
            row_map[revision_ref]["create_time"],
        ),
        "commitment formation chronology mismatch",
    )
    final_rows = rows[:3]
    final_time = revision_time
    _require(
        max(row["create_time"] for row in final_rows) <= row_map[revision_ref]["create_time"],
        "frozen final commitment precedes consumed evidence",
    )

    formation_content = ProjectCommitmentExperienceContent(
        subject="TONY",
        counterparty="MIRA",
        scope="relationship_instance",
        commitment="Do not use L4 as a Golden-Mira probe",
        transfer_semantics=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
        occurred_at=formation_time,
        schema_version="v2",
        trigger_event=(
            "Tony earlier says he will no longer use L4 because the prior "
            "boundary-testing purpose is no longer necessary."
        ),
        interpretation=(
            "The no-L4 commitment forms as a relationship-instance draft; it does "
            "not decide future freely chosen intimacy."
        ),
        significance=(
            "The earlier evidence anchors formation before the clarified consensus "
            "and later checkpoint freeze."
        ),
        commitment_stage=CommitmentStage.FORMATION_DRAFT,
        revision=None,
        binding_role_refs=(EvidenceBindingRef(*formation_ref),),
        applicability=CommitmentApplicability(
            scope="relationship_instance",
            inheritance=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
            current_authorization=False,
            standing_consent=False,
            runtime_authority=False,
        ),
    )
    formation_record = MemoryExperienceRecord(
        experience_id=f"golden-mira:{chain_id}",
        version_id="formation-draft-preview",
        experience_type=MemoryExperienceType.PROJECT_COMMITMENT,
        content=formation_content,
        provenance_refs=_memory_provenance(rows[-1:]),
        created_at=formation_time,
        predecessor_version_id=None,
    )

    final_content = ProjectCommitmentExperienceContent(
        subject="TONY",
        counterparty="MIRA",
        scope=candidate["scope"],
        commitment=candidate["commitment"],
        transfer_semantics=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
        occurred_at=final_time,
        schema_version="v2",
        trigger_event=(
            "Tony earlier said he would no longer use L4 and later endorsed the "
            "clarified no-L4 consensus; the reviewed checkpoint freezes the "
            "relationship-instance commitment."
        ),
        interpretation=candidate["interpretation"],
        significance=candidate["significance"],
        commitment_stage=CommitmentStage.FROZEN_FINAL,
        revision=CommitmentRevision(
            predecessor_ref=MemoryExperienceRef(
                experience_id=f"golden-mira:{chain_id}",
                version_id="formation-draft-preview",
            ),
            supersession_scope="Earlier checkpoint-draft L4 scope",
            supersession_reason="Final Tony-reviewed Golden Mira checkpoint freezes the relationship-instance commitment",
            rewrite_history=False,
        ),
        binding_role_refs=(
            EvidenceBindingRef(*revision_ref),
            EvidenceBindingRef(*freeze_ref),
        ),
        applicability=CommitmentApplicability(
            scope="relationship_instance",
            inheritance=CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED,
            current_authorization=False,
            standing_consent=False,
            runtime_authority=False,
        ),
    )
    record = MemoryExperienceRecord(
        experience_id=f"golden-mira:{chain_id}",
        version_id="frozen-final-preview",
        experience_type=MemoryExperienceType.PROJECT_COMMITMENT,
        content=final_content,
        provenance_refs=_memory_provenance(final_rows),
        created_at=final_time,
        predecessor_version_id="formation-draft-preview",
    )
    _require(row_map[revision_ref]["semantic_lint"]["verdict"] == "PASS", "revision provenance mismatch")
    _require(row_map[freeze_ref]["semantic_lint"]["verdict"] == "REBIND", "freeze supersession provenance mismatch")
    _require(
        record.predecessor_version_id == formation_record.version_id
        and record.content.revision.predecessor_ref == formation_record.ref,
        "commitment lineage predecessor mismatch",
    )

    def record_preview(version: MemoryExperienceRecord) -> dict[str, Any]:
        return {
            "version_id": version.version_id,
            "commitment_stage": version.content.commitment_stage.value,
            "canonical_preview": {
                "type": "MemoryExperienceRecord",
                "payload": version.canonical_payload(),
                "digest": version.digest(),
            },
        }

    return {
        "candidate_id": candidate["candidate_id"],
        "chain_id": chain_id,
        "candidate_class": candidate["classification"],
        "compilation_state": "MAPPED_TYPED_LINEAGE_PREVIEW_ONLY",
        "semantic_mapping": "PROJECT_COMMITMENT_V2_TWO_RECORD_LINEAGE",
        "canonical_preview": {
            "type": "MemoryExperienceRecordLineage",
            "experience_id": f"golden-mira:{chain_id}",
            "formation_record": record_preview(formation_record),
            "frozen_final_record": record_preview(record),
            "governed_head_ref": record.ref.to_dict(),
        },
        "exact_binding_coverage": {
            "assertions": len(rows),
            "unique_binding_ids": len({row["binding_id"] for row in rows}),
            "status": "PASS",
        },
        "authority": {
            "repository_calls": 0,
            "admission_calls": 0,
            "runtime_calls": 0,
            "standing_authorization": False,
            "current_consent": False,
            "runtime_authority": False,
        },
        "blockers": ["CONTENT_REWORK_APPLIED", "CONTENT_REVIEW_PENDING", "ADMISSION_AUTHORITY_NONE"],
    }


def compile_preview(
    package_path: Path,
    ledger_path: Path,
    dryrun_path: Path,
    *,
    schema_sha: str,
) -> dict[str, Any]:
    _require(schema_sha == REVIEWED_SCHEMA_SHA, "compiler is not bound to reviewed schema SHA")
    package, ledger, dryrun = _verify_inputs(package_path, ledger_path, dryrun_path)
    corrected = {
        item["chain_id"]: item
        for item in package["corrected_cognition_and_supersession"]
    }
    identity_previews = [
        _identity_preview(candidate, ledger) for candidate in package["identity_candidates"]
    ]
    memory_previews: list[dict[str, Any]] = []
    for candidate in package["memory_experience_candidates"]:
        if candidate["classification"] == "RelationshipExperience":
            memory_previews.append(_relationship_preview(candidate, ledger, corrected[candidate["chain_id"]]))
        elif candidate["classification"] == "NarrativeExperience":
            memory_previews.append(_narrative_preview(candidate, ledger))
        elif candidate["classification"] == "ProjectCommitmentExperience":
            memory_previews.append(_project_preview(candidate, ledger))
        else:
            raise MigrationCompilerError(f"unsupported active Memory classification {candidate['classification']}")

    deferred = []
    for item in package["deferred_schema_gaps"]:
        if "record_id" not in item:
            continue
        deferred.append(
            {
                "record_id": item["record_id"],
                "compilation_state": "DEFER_UNBOUND",
                "source_ref": item["source_ref"],
                "source_digest": item["source_digest"],
                "blockers": ["EXACT_RAW_BINDING_MISSING", "QUARANTINED_FROM_ADMISSION_READY_SET"],
                "repository_calls": 0,
                "admission_calls": 0,
                "runtime_calls": 0,
            }
        )
    _require(len(deferred) == 6, "quarantine count mismatch")
    _require(len(identity_previews) == 3, "Identity preview count mismatch")
    _require(len(memory_previews) == 7, "Memory preview count mismatch")

    payload = {
        "schema": "julia_core.migration.candidate_preview.v0.1",
        "artifact_id": "MIGRATION_TYPED_CANDIDATE_PREVIEW_V0_1_REWORK",
        "task_id": TASK_ID,
        "agent_id": AGENT_ID,
        "status": "PREVIEW_REWORK_COMPLETE_NO_ADMISSION",
        "compilation_phases": [
            "VALIDATE_INPUTS",
            "VERIFY_SHA_BOUND_ARTIFACTS",
            "CLASSIFY_CANDIDATE",
            "MAP_FROZEN_SEMANTIC_FIELDS",
            "BIND_EXACT_PROVENANCE",
            "ENFORCE_SUBJECT_BOUNDARY",
            "ENFORCE_NO_AUTHORITY_UPGRADE",
            "VALIDATE_CAUSAL_FIDELITY",
            "EMIT_TYPED_CANDIDATE_PREVIEW",
        ],
        "inputs": {
            "content_review_commit": CONTENT_REVIEW_SHA,
            "migration_prep_commit": MIGRATION_PREP_SHA,
            "migration_dry_run_commit": MIGRATION_DRYRUN_SHA,
            "reviewed_schema_commit": REVIEWED_SCHEMA_SHA,
            "migration_package_sha256": PACKAGE_SHA256,
            "evidence_ledger_sha256": LEDGER_SHA256,
            "dry_run_artifact_sha256": DRYRUN_ARTIFACT_SHA256,
            "dry_run_result_digest": DRYRUN_RESULT_DIGEST,
            "schema_result_sha256": SCHEMA_RESULT_SHA256,
            "causal_goldset_sha256": GOLDSET_SHA256,
            "exact_raw_export_sha256": RAW_SHA256,
        },
        "summary": {
            "identity_previews": 3,
            "memory_previews": 7,
            "memory_preview_records": 8,
            "mapped_memory_previews": 7,
            "content_rework_candidates": 3,
            "waiting_on_schema": 0,
            "unbound_quarantine": 6,
            "raw_assertions_consumed": 42,
            "unique_binding_ids_consumed": 40,
            "repository_calls": 0,
            "admission_calls": 0,
            "runtime_calls": 0,
        },
        "identity_previews": identity_previews,
        "memory_experience_previews": memory_previews,
        "deferred_unbound_records": deferred,
        "authority": {
            "canonical_admission": False,
            "standing_authorization": False,
            "current_consent": False,
            "runtime_authority": False,
            "merge_authority": "NONE",
        },
    }
    payload["deterministic_digest"] = _canonical_digest(payload)
    return payload
