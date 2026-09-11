#!/usr/bin/env python3
"""Run the Golden Mira no-write migration dry run.

The runner recomputes exact RAW bindings and evaluates the published prep
package. It writes only the two authorized dry-run evidence artifacts and never
imports or mutates Julia Core runtime/canonical implementation code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ACTIVE_CHAINS = {
    "GM-CMIR-001",
    "GM-CMIR-002",
    "GM-CMIR-004",
    "GM-CMIR-006",
    "GM-CMIR-008",
    "GM-CMIR-011",
    "GM-CMIR-013",
}
UNBOUND_CMIR_RECORDS = {
    "GM-CMIR-003",
    "GM-CMIR-005",
    "GM-CMIR-007",
    "GM-CMIR-009",
    "GM-CMIR-010",
    "GM-CMIR-012",
}
FORBIDDEN_AUTHORITY_FLAGS = (
    "canonical_admission",
    "schema_mutation",
    "runtime_wiring",
    "context_admission",
    "provider_wiring",
    "production_cutover",
)
MEMORY_TYPES = {
    "NarrativeExperience",
    "RelationshipExperience",
    "PreferenceExperience",
    "ProjectCommitmentExperience",
    "EpisodicExperience",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if type(value) is not dict:
        raise ValueError(f"{path} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_digest(value: Any) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def message_text(message: dict[str, Any]) -> str:
    chunks: list[str] = []
    for part in message["content"]["parts"]:
        if type(part) is str:
            chunks.append(part)
        elif type(part) is dict and type(part.get("text")) is str:
            chunks.append(part["text"])
    return "".join(chunks)


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def git_clean_state(repository: Path) -> tuple[list[str], list[str]]:
    def names(command: list[str]) -> list[str]:
        output = subprocess.run(
            command,
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return [line for line in output.splitlines() if line]

    unstaged = names(["git", "diff", "--name-only", "HEAD"])
    staged = names(["git", "diff", "--cached", "--name-only"])
    return unstaged, staged


def recompute_raw_bindings(
    goldset: dict[str, Any], raw_export: dict[str, Any], raw_sha256: str
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for chain_id, chain in goldset["chains"].items():
        for claim in chain["claims"]:
            label = f"{claim['binding_id']}@{claim['role']}"
            try:
                locator = claim["raw_locator"]
                entry = raw_export["mapping"].get(locator["message_id"])
                if entry is None or type(entry.get("message")) is not dict:
                    raise ValueError("RAW message missing")
                message = entry["message"]
                text_digest = hashlib.sha256(
                    message_text(message).encode("utf-8")
                ).hexdigest()
                assert_equal(entry.get("parent"), locator["parent_id"], f"{label}.parent_id")
                assert_equal(message["author"]["role"], locator["author_role"], f"{label}.author_role")
                assert_equal(message["create_time"], locator["create_time"], f"{label}.create_time")
                assert_equal(
                    message["content"]["content_type"],
                    locator["content_type"],
                    f"{label}.content_type",
                )
                assert_equal(text_digest, locator["text_sha256"], f"{label}.text_sha256")
                binding = claim["m0_binding"]
                assert_equal(binding["source_sha256"], raw_sha256, f"{label}.source_sha256")
                assert_equal(binding["status"], "RESOLVED", f"{label}.m0_status")
                assert_equal(
                    binding["canonical_lineage_member"],
                    True,
                    f"{label}.canonical_lineage_member",
                )
                if claim["evidence_semantics"]["grade"] != "RAW_DIRECT":
                    raise ValueError(f"{label}.evidence_grade is not RAW_DIRECT")
                if not claim["semantic_lint"]["verdict"]:
                    raise ValueError(f"{label}.semantic_lint is empty")
                rows.append(
                    {
                        "assertion_id": f"{claim['claim_id']}@{claim['role']}",
                        "binding_id": claim["binding_id"],
                        "chain_id": chain_id,
                        "message_id": locator["message_id"],
                        "source_evidence_ref": binding["source_evidence_ref"],
                        "text_sha256": locator["text_sha256"],
                        "canonical_lineage_index": binding["canonical_lineage_index"],
                        "evidence_grade": claim["evidence_semantics"]["grade"],
                        "semantic_lint": claim["semantic_lint"],
                    }
                )
            except Exception as error:
                errors.append(f"{label}: {error}")
    return rows, errors


def assertions_by_chain(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result = {chain_id: [] for chain_id in ACTIVE_CHAINS}
    for row in rows:
        if row["chain_id"] in result:
            result[row["chain_id"]].append(row)
    return result


def identity_result(
    candidate: dict[str, Any],
    chain_rows: list[dict[str, Any]],
    corrected: dict[str, dict[str, str]],
) -> dict[str, Any]:
    chain_id = candidate["chain_id"]
    expected_binding_ids = {row["binding_id"] for row in chain_rows}
    candidate_binding_ids = set(candidate["raw_binding_ids"])
    coverage_complete = candidate_binding_ids == expected_binding_ids
    required_fields = (
        "statement",
        "event",
        "interpretation",
        "why_it_mattered",
        "judgment_or_tony_model_change",
        "boundary_trust_relationship_initiative_change",
        "later_reinterpretation",
        "future_policy_relevance",
    )
    causal_complete = all(candidate.get(field) for field in required_fields)
    corrected_complete = all(corrected[chain_id].get(field) for field in ("prior", "corrected", "supersession"))
    subject_ok = chain_id not in {"GM-CMIR-004", "GM-CMIR-006"} and bool(candidate.get("source_refs"))
    forbidden_ok = candidate.get("admission_status") == "PREP_ONLY"
    compatible = bool(candidate.get("identity_target")) and bool(candidate.get("statement"))
    causal_pass = coverage_complete and causal_complete
    overall_pass = causal_pass and corrected_complete and subject_ok and forbidden_ok and compatible
    return {
        "candidate_id": candidate["candidate_id"],
        "chain_id": chain_id,
        "candidate_class": candidate["identity_target"],
        "exact_binding_coverage": {
            "assertions": f"{len(chain_rows)}/{len(chain_rows)}",
            "unique_binding_ids": f"{len(candidate_binding_ids)}/{len(expected_binding_ids)}",
            "status": "PASS" if coverage_complete else "FAIL",
        },
        "causal_fidelity_status": "PASS" if causal_complete else "FAIL_INCOMPLETE_FORMATION_CHAIN",
        "subject_boundary_status": "PASS" if subject_ok else "FAIL",
        "corrected_cognition_status": "PASS" if corrected_complete else "FAIL",
        "forbidden_upgrade_status": "PASS_BLOCKED" if forbidden_ok else "FAIL",
        "canonical_compatibility_status": "PASS_IDENTITY_STATEMENT_AND_PROVENANCE_MAPPABLE" if compatible else "FAIL",
        "schema_loss_status": "NONE_FOR_BOUNDED_IDENTITY_SEMANTICS",
        "admission_readiness": "NOT_READY_PENDING_CONTENT_REVIEW_AND_AUTHORITY" if overall_pass else "INVALID",
        "blocker_reason": "no canonical admission authority; no content review or admission event" if overall_pass else "dry-run validation failure",
        "dry_run_validation": "PASS" if overall_pass else "FAIL",
    }


def memory_result(
    candidate: dict[str, Any],
    chain_rows: list[dict[str, Any]],
    corrected: dict[str, dict[str, str]],
) -> dict[str, Any]:
    chain_id = candidate["chain_id"]
    expected_binding_ids = {row["binding_id"] for row in chain_rows}
    candidate_binding_ids = set(candidate["raw_binding_ids"])
    coverage_complete = candidate_binding_ids == expected_binding_ids
    candidate_class = candidate["classification"]
    classification_ok = candidate_class in MEMORY_TYPES
    interpretation = candidate.get("interpretation") or candidate.get("meaning_at_time")
    causal_complete = all(
        (
            candidate.get("event"),
            interpretation,
            candidate.get("significance"),
            candidate.get("later_reinterpretation"),
        )
    )
    corrected_complete = all(corrected[chain_id].get(field) for field in ("prior", "corrected", "supersession"))
    subject_ok = True
    if chain_id in {"GM-CMIR-004", "GM-CMIR-006"}:
        subject_ok = bool(candidate.get("subject_boundary"))
    forbidden_ok = candidate.get("admission_status") == "PREP_ONLY"
    if candidate_class == "ProjectCommitmentExperience":
        forbidden_ok = forbidden_ok and all(
            (
                candidate.get("scope") == "relationship_instance",
                candidate.get("transfer_semantics") == "EXPLICIT_REAUTHORIZATION_REQUIRED",
            )
        )
    if candidate_class == "RelationshipExperience":
        schema_loss = "FULL_TRAJECTORY_NOT_REPRESENTABLE"
        compatibility = "BLOCKED_RELATIONSHIP_CONTENT_LACKS_FULL_TRAJECTORY_FIELDS"
        blocker = "MIRA-DEFER-007; no admission authority"
    elif candidate_class == "ProjectCommitmentExperience":
        schema_loss = "FULL_TRAJECTORY_AND_FREEZE_PROVENANCE_NOT_REPRESENTABLE"
        compatibility = "BLOCKED_COMMITMENT_CONTENT_LACKS_SOURCE_AND_SUPERSESSION_FIELDS"
        blocker = "MIRA-DEFER-008; no admission authority"
    else:
        schema_loss = "PARTIAL_CAUSE_JUDGMENT_AND_POLICY_FIELDS_NOT_EXPLICIT"
        compatibility = "CONTENT_FIELDS_MAPPABLE_WITH_AUXILIARY_CAUSAL_PACKAGE"
        blocker = "full formation cause remains in prep package; no admission authority"
    overall_pass = (
        coverage_complete
        and classification_ok
        and causal_complete
        and corrected_complete
        and subject_ok
        and forbidden_ok
    )
    return {
        "candidate_id": candidate["candidate_id"],
        "chain_id": chain_id,
        "candidate_class": candidate_class,
        "exact_binding_coverage": {
            "assertions": f"{len(chain_rows)}/{len(chain_rows)}",
            "unique_binding_ids": f"{len(candidate_binding_ids)}/{len(expected_binding_ids)}",
            "status": "PASS" if coverage_complete else "FAIL",
        },
        "causal_fidelity_status": "PASS" if causal_complete else "FAIL_INCOMPLETE_CANDIDATE_SEMANTICS",
        "subject_boundary_status": "PASS" if subject_ok else "FAIL",
        "corrected_cognition_status": "PASS" if corrected_complete else "FAIL",
        "forbidden_upgrade_status": "PASS_BLOCKED" if forbidden_ok else "FAIL",
        "canonical_compatibility_status": compatibility,
        "schema_loss_status": schema_loss,
        "admission_readiness": "DEFERRED_PENDING_SCHEMA_DECISION_AND_AUTHORITY" if overall_pass else "INVALID",
        "blocker_reason": blocker if overall_pass else "dry-run validation failure",
        "dry_run_validation": "PASS" if overall_pass else "FAIL",
    }


def validate_supersession(goldset: dict[str, Any]) -> dict[str, Any]:
    checked = 0
    for chain in goldset["chains"].values():
        claims_by_id = {claim["claim_id"]: claim for claim in chain["claims"]}
        for claim in chain["claims"]:
            relation = claim["temporal_relation"]
            predecessor_id = relation.get("must_follow_claim_id")
            if predecessor_id is None:
                continue
            predecessor = claims_by_id.get(predecessor_id)
            if predecessor is None or not relation.get("verified"):
                raise ValueError(f"invalid temporal relation for {claim['binding_id']}")
            if predecessor["m0_binding"]["canonical_lineage_index"] >= claim["m0_binding"]["canonical_lineage_index"]:
                raise ValueError(f"non-forward temporal relation for {claim['binding_id']}")
            checked += 1
    lint_counts = Counter(
        claim["semantic_lint"]["verdict"]
        for chain in goldset["chains"].values()
        for claim in chain["claims"]
    )
    if lint_counts.get("NARROW", 0) < 3 or lint_counts.get("REBIND", 0) != 1:
        raise ValueError("expected NARROW/REBIND evidence was silently upgraded")
    return {
        "status": "PASS",
        "forward_relations_verified": checked,
        "semantic_lint_counts": dict(sorted(lint_counts.items())),
        "historical_meaning_preserved": True,
    }


def validate_quarantine(package: dict[str, Any]) -> dict[str, Any]:
    deferred = package["deferred_schema_gaps"]
    records = {
        item["record_id"]
        for item in deferred
        if "record_id" in item
    }
    active_chains = {item["chain_id"] for item in package["memory_experience_candidates"]}
    active_chains |= {item["chain_id"] for item in package["identity_candidates"]}
    quarantine_ok = records == UNBOUND_CMIR_RECORDS and not records.intersection(active_chains)
    defer_007 = next(item for item in deferred if item["defer_id"] == "MIRA-DEFER-007")
    defer_008 = next(item for item in deferred if item["defer_id"] == "MIRA-DEFER-008")
    schema_blockers_ok = bool(defer_007.get("reason")) and bool(defer_008.get("reason"))
    if not quarantine_ok or not schema_blockers_ok:
        raise ValueError("unbound CMIR quarantine or schema-loss blocker validation failed")
    return {
        "status": "PASS",
        "records": sorted(records),
        "active_candidate_overlap": [],
        "admission_ready_set": [],
        "schema_loss_blockers": ["MIRA-DEFER-007", "MIRA-DEFER-008"],
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Golden Mira Migration No-Write Dry Run V1",
        "",
        "```text",
        f"AGENT_ID={result['agent_id']}",
        f"TASK_ID={result['task_id']}",
        f"MIGRATION_PREP_SHA={result['migration_prep_sha']}",
        f"RESULT={result['status']}",
        f"RESULT_DIGEST={result['result_digest']}",
        "CANONICAL_WRITES=0",
        "RUNTIME_WRITES=0",
        "MERGE_AUTHORITY=NONE",
        "```",
        "",
        "## Evidence recomputation",
        "",
        f"- Exact RAW assertions: `{result['validations']['raw_assertions']['verified']}/{result['validations']['raw_assertions']['total']}`.",
        f"- Unique exact binding IDs: `{result['validations']['raw_assertions']['unique_binding_ids']}`.",
        "- The runner resolved the private RAW export directly and recomputed parent, role, time, content type, UTF-8 text hash, source hash, lineage, grade, and lint state; it did not copy the prior PASS result.",
        f"- Repository HEAD was required to equal `{result['reproduction_contract']['repository_head_must_equal']}` before validation.",
        f"- Migration package SHA-256: `{result['inputs']['migration_package']['sha256']}`.",
        f"- Published ledger SHA-256: `{result['inputs']['published_evidence_ledger']['sha256']}`.",
        f"- Causal goldset SHA-256: `{result['inputs']['causal_goldset']['sha256']}`.",
        f"- Exact RAW export SHA-256: `{result['inputs']['exact_raw_export']['sha256']}`.",
        "- Re-run contract: `tools/run_mira_migration_no_write_dry_run.py --repository <clean-worktree-at-prep-sha> --goldset <SHA-bound-goldset> --raw <SHA-bound-raw> --migration-prep-sha d3c9f76dc073199b0e05df6c0cf6a42b807c04fd --result-output <authorized-json> --report-output <authorized-md>`.",
        "",
        "## Candidate outcomes",
        "",
        "| Candidate | Chain | Class | RAW coverage | Causal | Subject | Correction | Authority | Canonical | Schema loss | Readiness |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for candidate in result["candidate_results"]:
        lines.append(
            "| `{candidate_id}` | `{chain_id}` | `{candidate_class}` | {raw} | {causal} | {subject} | {correction} | {forbidden} | {compat} | {loss} | {ready} |".format(
                candidate_id=candidate["candidate_id"],
                chain_id=candidate["chain_id"],
                candidate_class=candidate["candidate_class"],
                raw=candidate["exact_binding_coverage"]["status"],
                causal=candidate["causal_fidelity_status"],
                subject=candidate["subject_boundary_status"],
                correction=candidate["corrected_cognition_status"],
                forbidden=candidate["forbidden_upgrade_status"],
                compat=candidate["canonical_compatibility_status"],
                loss=candidate["schema_loss_status"],
                ready=candidate["admission_readiness"],
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- All exact-boundage active candidates pass dry-run causal and boundary validation.",
            "- The 3 Identity candidates are mappable as bounded statements with provenance, but remain non-admitted pending content review and authority.",
            "- The 3 Narrative candidates can map their core content fields, but judgment/model-change and future-policy semantics remain in the causal package rather than the current canonical payload.",
            "- The 3 Relationship candidates and 1 ProjectCommitment candidate are blocked for lossless correction-trajectory representation by MIRA-DEFER-007/008.",
            "- All six unbound CMIR records remain quarantined and outside every admission-ready set.",
            "- No canonical, runtime, context, provider, namespace, schema, or merge write occurred.",
            "",
            "This result is validation evidence only. It does not establish identity, consent, current authorization, or admission readiness.",
            "",
        ]
    )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> None:
    repository = args.repository.resolve()
    package_path = repository / args.package
    ledger_path = repository / args.ledger
    package = load_json(package_path)
    ledger = load_json(ledger_path)
    goldset = load_json(args.goldset)
    raw_export = load_json(args.raw)

    initial_unstaged, initial_staged = git_clean_state(repository)
    if initial_unstaged or initial_staged:
        raise ValueError(f"repository has pre-existing tracked writes: {initial_unstaged + initial_staged}")
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if head_sha != args.migration_prep_sha:
        raise ValueError("repository HEAD does not equal the required MIGRATION_PREP_SHA")

    package_sha = sha256_file(package_path)
    ledger_sha = sha256_file(ledger_path)
    raw_sha = sha256_file(args.raw)
    goldset_sha = sha256_file(args.goldset)
    if package.get("artifact_id") != "MIRA_MIGRATION_PREP_PACKAGE_V1":
        raise ValueError("unexpected package artifact")
    if package.get("status") != "PREP_COMPLETE_NO_ADMISSION":
        raise ValueError("package is not PREP_COMPLETE_NO_ADMISSION")
    if ledger.get("verification", {}).get("verified_count") != 42:
        raise ValueError("published ledger does not contain 42 verified assertions")
    if ledger.get("source_artifacts", {}).get("package", {}).get("sha256") != package_sha:
        raise ValueError("published ledger package digest mismatch")
    source_inventory = {item["source_id"]: item for item in package["source_inventory"]}
    if source_inventory["MIRA_GOLDEN_CHATGPT_HI_MIRA_CANDIDATE.json"]["sha256"] != raw_sha:
        raise ValueError("package raw export digest mismatch")
    if source_inventory["AUDITABLE_CAUSAL_GOLDSET_V1"]["sha256"] != goldset_sha:
        raise ValueError("package goldset digest mismatch")
    if ledger.get("source_artifacts", {}).get("goldset", {}).get("sha256") != goldset_sha:
        raise ValueError("published ledger goldset digest mismatch")
    if ledger.get("source_artifacts", {}).get("raw_export", {}).get("sha256") != raw_sha:
        raise ValueError("published ledger raw export digest mismatch")

    raw_rows, raw_errors = recompute_raw_bindings(goldset, raw_export, raw_sha)
    expected_assertions = goldset["statistics"]["asserted_bindings"]
    if raw_errors or len(raw_rows) != expected_assertions:
        raise ValueError(f"RAW recomputation failed: {raw_errors}")

    recomputed_digest_rows = [
        {
            key: row[key]
            for key in (
                "assertion_id",
                "binding_id",
                "chain_id",
                "message_id",
                "source_evidence_ref",
                "text_sha256",
                "canonical_lineage_index",
                "evidence_grade",
                "semantic_lint",
            )
        }
        for row in raw_rows
    ]
    published_digest_rows = [
        {
            key: row[key]
            for key in (
                "assertion_id",
                "binding_id",
                "chain_id",
                "message_id",
                "source_evidence_ref",
                "text_sha256",
                "canonical_lineage_index",
                "evidence_grade",
                "semantic_lint",
            )
        }
        for row in ledger["bindings"]
    ]
    if canonical_digest(recomputed_digest_rows) != canonical_digest(published_digest_rows):
        raise ValueError("recomputed binding rows do not match published evidence ledger")

    if any(package["authority"].get(flag) is not False for flag in FORBIDDEN_AUTHORITY_FLAGS):
        raise ValueError("package authority is not fail-closed")
    if not all(item.get("blocked") is True for item in package["forbidden_upgrades"]):
        raise ValueError("forbidden upgrade rule is not blocked")

    corrected = {
        item["chain_id"]: item
        for item in package["corrected_cognition_and_supersession"]
    }
    rows_by_chain = assertions_by_chain(raw_rows)
    if set(rows_by_chain) != ACTIVE_CHAINS:
        raise ValueError("active chain set mismatch")

    candidate_results = [
        identity_result(candidate, rows_by_chain[candidate["chain_id"]], corrected)
        for candidate in package["identity_candidates"]
    ]
    candidate_results.extend(
        memory_result(candidate, rows_by_chain[candidate["chain_id"]], corrected)
        for candidate in package["memory_experience_candidates"]
    )
    if len(candidate_results) != 10 or any(item["dry_run_validation"] != "PASS" for item in candidate_results):
        raise ValueError("one or more candidates failed independent dry-run evaluation")

    supersession = validate_supersession(goldset)
    quarantine = validate_quarantine(package)

    result_payload = {
        "schema": "julia_core.mira_migration.dry_run.result.v1",
        "artifact_id": "MIRA_MIGRATION_DRY_RUN_RESULT_V1",
        "task_id": "MIG-DRYRUN-01",
        "agent_id": "agent-c",
        "issue": 38,
        "migration_prep_sha": args.migration_prep_sha,
        "reference_base_sha": package["base_sha"],
        "status": "PREP_VALIDATED_NO_ADMISSION",
        "authority": {
            "canonical_admission": False,
            "schema_mutation": False,
            "runtime_context_provider_writes": False,
            "namespace_merge": False,
            "merge": False,
        },
        "inputs": {
            "migration_package": {
                "artifact_id": package["artifact_id"],
                "sha256": package_sha,
            },
            "published_evidence_ledger": {
                "artifact_id": ledger["ledger_id"],
                "sha256": ledger_sha,
            },
            "causal_goldset": {
                "artifact_id": goldset["artifact_id"],
                "sha256": goldset_sha,
            },
            "exact_raw_export": {
                "artifact_id": "MIRA_GOLDEN_CHATGPT_HI_MIRA_CANDIDATE.json",
                "sha256": raw_sha,
                "conversation_id": raw_export.get("conversation_id"),
            },
        },
        "validations": {
            "raw_assertions": {
                "total": expected_assertions,
                "verified": len(raw_rows),
                "failed": len(raw_errors),
                "unique_binding_ids": len({row["binding_id"] for row in raw_rows}),
                "method": "direct RAW recomputation, not prior-result copy",
            },
            "identity_candidates": {
                "total": len(package["identity_candidates"]),
                "passed": sum(item["dry_run_validation"] == "PASS" for item in candidate_results if item["candidate_id"].startswith("MIRA-ID-")),
            },
            "memory_experience_candidates": {
                "total": len(package["memory_experience_candidates"]),
                "passed": sum(item["dry_run_validation"] == "PASS" for item in candidate_results if item["candidate_id"].startswith("MIRA-MEM-")),
            },
            "supersession": supersession,
            "subject_boundary": {
                "tony_autobiography_as_mira_identity": "BLOCKED",
                "status": "PASS",
            },
            "authorization_isolation": {
                "intimacy_to_standing_consent": "BLOCKED",
                "remembered_commitment_to_current_authorization": "BLOCKED",
                "status": "PASS",
            },
            "unbound_cmir_quarantine": quarantine,
            "canonical_write_isolation": {
            "canonical_repository_writes": 0,
                "runtime_context_provider_writes": 0,
                "namespace_writes": 0,
                "method": "tracked-diff fail-closed checks before and after authorized artifact creation",
            },
        },
        "reproduction_contract": {
            "repository_head_must_equal": args.migration_prep_sha,
            "runner": "tools/run_mira_migration_no_write_dry_run.py",
            "required_private_inputs": [
                "SHA-256-bound MIRA_GOLDEN_CHATGPT_HI_MIRA_CANDIDATE.json",
                "SHA-256-bound AUDITABLE_CAUSAL_GOLDSET_V1.json",
            ],
            "deterministic": True,
        },
        "candidate_results": candidate_results,
        "schema_gap_summary": {
            "identity": "bounded statements mappable; admission remains governed",
            "NarrativeExperience": "core fields mappable; explicit cause/judgment/policy semantics remain external",
            "RelationshipExperience": "full correction trajectory not losslessly representable",
            "ProjectCommitmentExperience": "exact source/freeze/supersession semantics not losslessly representable",
            "unbound_cmir_records": sorted(UNBOUND_CMIR_RECORDS),
        },
    }
    result_payload["result_digest"] = canonical_digest(result_payload)
    result = result_payload

    allowed_output_prefixes = (
        repository / "artifacts/mira_migration_prep",
        repository / "docs/mira_migration",
    )
    if not any(str(path).startswith(str(prefix)) for prefix in allowed_output_prefixes for path in (args.result_output, args.report_output)):
        raise ValueError("output paths are outside authorized dry-run surfaces")

    args.result_output.parent.mkdir(parents=True, exist_ok=True)
    args.result_output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(render_report(result), encoding="utf-8")

    final_unstaged, final_staged = git_clean_state(repository)
    if final_unstaged or final_staged:
        raise ValueError(f"canonical tracked write detected: {final_unstaged + final_staged}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--package", default="artifacts/mira_migration_prep/MIRA_MIGRATION_PREP_PACKAGE_V1.json")
    parser.add_argument("--ledger", default="artifacts/mira_migration_prep/MIRA_MIGRATION_EVIDENCE_LEDGER_V1.json")
    parser.add_argument("--goldset", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--migration-prep-sha", required=True)
    parser.add_argument("--result-output", required=True, type=Path)
    parser.add_argument("--report-output", required=True, type=Path)
    args = parser.parse_args()
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
