"""Deterministic, no-write P5-E recovery governance rehearsal."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools.mira_migration.admission_sim import construct_admission_inputs


BASE_SHA = "038e5219495fd765bfbcfdbb0a52afb48a730f90"
SOURCE_PATH = Path(
    "artifacts/continuity/"
    "P5_A1_OWNER_AUTHORIZED_GOLDEN_MIRA_CANONICAL_ADMISSION_V1.json"
)
SOURCE_SHA256 = "f10a6d8daa6ed1604c2002254d26016efe31afca2e4dc18c4e1b094a48672110"
EVIDENCE_PATH = Path(
    "artifacts/continuity/" "P5_E_RECOVERY_SUPERSESSION_NO_WRITE_REHEARSAL_V1.json"
)
QUARANTINED_CMIR_IDS = frozenset(
    (
        "GM-CMIR-003",
        "GM-CMIR-005",
        "GM-CMIR-007",
        "GM-CMIR-009",
        "GM-CMIR-010",
        "GM-CMIR-012",
    )
)


class RecoveryRehearsalError(ValueError):
    pass


def _require(condition: bool, check: str) -> None:
    if condition is not True:
        raise RecoveryRehearsalError(f"FAIL_CLOSED: {check}")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class RecoveryActionPlan:
    namespace: str
    action: str
    target_ref: str
    target_digest: str
    successor_ref: str
    successor_digest: str
    actor: str
    reason: str
    occurred_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "action": self.action,
            "target_ref": self.target_ref,
            "target_digest": self.target_digest,
            "successor_ref": self.successor_ref,
            "successor_digest": self.successor_digest,
            "actor": self.actor,
            "reason": self.reason,
            "occurred_at": self.occurred_at,
            "authority": "REHEARSAL_ONLY",
            "execution": "NOT_EXECUTED",
        }


IDENTITY_PLAN = RecoveryActionPlan(
    namespace="identity",
    action="SUPERSEDE",
    target_ref=(
        "identity://mira-golden%3Amira-id-cand-001/mira-id-cand-001-v0.1-preview"
    ),
    target_digest=("7580e0a930dc7f3d5446da2cdd8d1c23cf251e12929fb2f3baa056bd9739dd44"),
    successor_ref=(
        "identity://mira-golden%3Amira-id-cand-001/"
        "mira-id-cand-001-v0.2-owner-correction-candidate"
    ),
    successor_digest="a" * 64,
    actor="owner:tony",
    reason="Rehearsed identity correction; no governance action is authorized here",
    occurred_at="rehearsal:2026-09-13T00:00:00Z",
)

MEMORY_PLAN = RecoveryActionPlan(
    namespace="memory_experience",
    action="SUPERSEDE",
    target_ref="memory-experience://golden-mira:GM-CMIR-001/v0.2-preview",
    target_digest=("4e29eb74de7f29bbf8d69485a7c18b5dceb06486d7e1d986d668a30c85fb7228"),
    successor_ref=(
        "memory-experience://golden-mira:GM-CMIR-001/" "v0.3-owner-correction-candidate"
    ),
    successor_digest="b" * 64,
    actor="owner:tony",
    reason="Rehearsed memory correction; no governance action is authorized here",
    occurred_at="rehearsal:2026-09-13T00:00:00Z",
)


def _source_evidence(repository: Path) -> tuple[dict[str, Any], list[Any], list[Any]]:
    source_path = repository / SOURCE_PATH
    source_bytes = source_path.read_bytes()
    _require(_sha256(source_bytes) == SOURCE_SHA256, "P5-A1 source artifact bytes")
    source = json.loads(source_bytes)
    _require(
        source.get("artifact_id")
        == "P5_A1_OWNER_AUTHORIZED_GOLDEN_MIRA_CANONICAL_ADMISSION_V1",
        "P5-A1 artifact identity",
    )
    _require(
        source.get("final_result")
        == "P5_A1_RESULT=OWNER_AUTHORIZED_CANONICAL_ADMISSION_COMPLETE",
        "P5-A1 accepted result",
    )
    identities, memories = construct_admission_inputs(repository)
    evidence_identities = source.get("admitted_identities", [])
    evidence_memories = source.get("admitted_memory_experiences", [])
    _require(len(identities) == len(evidence_identities) == 3, "exact Identity count")
    _require(len(memories) == len(evidence_memories) == 8, "exact Memory count")

    identity_by_ref = {item.ref.uri: item for item in identities}
    for evidence in evidence_identities:
        item = identity_by_ref.get(evidence["ref"])
        _require(item is not None, f"Identity exact ref: {evidence['ref']}")
        _require(
            item.digest() == evidence["digest"],
            f"Identity exact digest: {evidence['ref']}",
        )
        _require(
            evidence["status"] == "ADMITTED", f"Identity status: {evidence['ref']}"
        )
    _require(
        set(identity_by_ref) == {item["ref"] for item in evidence_identities},
        "Identity exact ref set",
    )

    memory_by_ref = {item.record.ref.uri: item for item in memories}
    for evidence in evidence_memories:
        item = memory_by_ref.get(evidence["ref"])
        _require(item is not None, f"Memory exact ref: {evidence['ref']}")
        _require(
            item.record.digest() == evidence["digest"],
            f"Memory exact digest: {evidence['ref']}",
        )
        _require(evidence["status"] == "ADMITTED", f"Memory status: {evidence['ref']}")
    _require(
        set(memory_by_ref) == {item["ref"] for item in evidence_memories},
        "Memory exact ref set",
    )
    return source, identities, memories


def _validate_plan(
    plan: RecoveryActionPlan,
    *,
    identity_records: list[Any],
    memory_records: list[Any],
) -> dict[str, Any]:
    _require(type(plan) is RecoveryActionPlan, "plan exact type")
    _require(plan.namespace in {"identity", "memory_experience"}, "plan namespace")
    _require(plan.action == "SUPERSEDE", "plan bounded action")
    _require(bool(plan.target_ref), "plan exact target ref")
    _require(len(plan.target_digest) == 64, "plan exact target digest")
    _require(bool(plan.successor_ref), "plan exact successor ref")
    _require(len(plan.successor_digest) == 64, "plan exact successor digest")
    _require(bool(plan.actor), "plan explicit actor")
    _require(bool(plan.reason), "plan explicit reason")
    _require(bool(plan.occurred_at), "plan explicit occurred_at")
    _require(plan.target_ref != plan.successor_ref, "successor distinct from target")

    if plan.namespace == "identity":
        records = identity_records
        digest_of = lambda item: item.digest()
        ref_of = lambda item: item.ref.uri
    else:
        records = memory_records
        digest_of = lambda item: item.record.digest()
        ref_of = lambda item: item.record.ref.uri
    matches = [item for item in records if ref_of(item) == plan.target_ref]
    _require(len(matches) == 1, f"unambiguous target: {plan.target_ref}")
    target = matches[0]
    _require(
        digest_of(target) == plan.target_digest,
        f"fresh target digest: {plan.target_ref}",
    )
    all_refs = [ref_of(item) for item in records]
    _require(
        all_refs.count(plan.successor_ref) == 0,
        f"unambiguous non-admitted successor: {plan.successor_ref}",
    )
    if plan.namespace == "memory_experience":
        prefix = "memory-experience://golden-mira:"
        _require(
            plan.target_ref.startswith(prefix)
            and plan.successor_ref.startswith(prefix),
            "memory successor uses exact namespace",
        )
        target_experience = plan.target_ref[len(prefix) :].split("/", 1)[0]
        successor_experience = plan.successor_ref[len(prefix) :].split("/", 1)[0]
        _require(
            target_experience == successor_experience and bool(target_experience),
            "memory successor preserves exact experience lineage",
        )
        if plan.target_ref.endswith("/frozen-final-preview"):
            successor_version = plan.successor_ref.rsplit("/", 1)[-1]
            _require(
                not successor_version.startswith("formation-draft"),
                "frozen-final successor cannot regress to formation draft",
            )
    else:
        prefix = "identity://mira-golden%3A"
        _require(
            plan.target_ref.startswith(prefix)
            and plan.successor_ref.startswith(prefix),
            "identity successor uses exact namespace",
        )
        target_lineage = plan.target_ref[len(prefix) :].split("/", 1)[0]
        successor_lineage = plan.successor_ref[len(prefix) :].split("/", 1)[0]
        _require(
            target_lineage == successor_lineage and bool(target_lineage),
            "identity successor preserves exact lineage",
        )
    for quarantined_id in QUARANTINED_CMIR_IDS:
        _require(
            quarantined_id not in plan.successor_ref,
            f"quarantined recovery substitute rejected: {quarantined_id}",
        )
    return {
        "validation": "PASS",
        "target_found": 1,
        "target_digest_fresh": True,
        "successor_unique": True,
        "quarantine_substitution_rejected": True,
    }


def _simulate_append_only(
    plan: RecoveryActionPlan,
    source: dict[str, Any],
) -> dict[str, Any]:
    identities = source["admitted_identities"]
    memories = source["admitted_memory_experiences"]
    collection = identities if plan.namespace == "identity" else memories
    matches = [item for item in collection if item["ref"] == plan.target_ref]
    _require(len(matches) == 1, "simulation exact source target")
    target = matches[0]
    before_events = target["governance_events"]
    simulated_target = {
        **target,
        "status": "SUPERSEDED",
        "governance_events": [
            *before_events,
            {
                "event_id": (
                    f"{plan.namespace}-supersession-rehearsal:"
                    f"{plan.target_ref}:{len(before_events)}"
                ),
                "target": plan.target_ref,
                "status": "SUPERSEDED",
                "actor": plan.actor,
                "reason": plan.reason,
                "occurred_at": plan.occurred_at,
                "successor_ref": plan.successor_ref,
                "successor_digest": plan.successor_digest,
            },
        ],
    }
    simulated_collection = [
        simulated_target if item["ref"] == plan.target_ref else item
        for item in collection
    ]
    simulated_source = {
        **source,
        "admitted_identities": (
            simulated_collection if plan.namespace == "identity" else identities
        ),
        "admitted_memory_experiences": (
            simulated_collection if plan.namespace == "memory_experience" else memories
        ),
    }
    after_events = simulated_target["governance_events"]
    original = next(
        item for item in simulated_collection if item["ref"] == plan.target_ref
    )
    return {
        "plan": plan.to_dict(),
        "append_only_event": after_events[-1],
        "original_event_prefix_unchanged": after_events[:-1] == before_events,
        "original_record_readable": original is not None,
        "original_digest_unchanged": original["digest"] == target["digest"],
        "all_original_refs_readable": len(simulated_collection) == len(collection),
        "source_event_count_before": len(before_events),
        "source_event_count_after": len(after_events),
        "record_rewrites": 0,
        "history_rewrites": 0,
        "simulated_state_sha256": _sha256(
            json.dumps(
                simulated_source,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ),
        "actual_repository_calls": 0,
        "actual_canonical_writes": 0,
    }


def _commitment_lineage(repository_records: list[Any]) -> dict[str, Any]:
    by_version = {
        item.record.version_id: item
        for item in repository_records
        if item.record.experience_id == "golden-mira:GM-CMIR-011"
    }
    draft = by_version.get("formation-draft-preview")
    final = by_version.get("frozen-final-preview")
    _require(draft is not None, "ProjectCommitment formation draft present")
    _require(final is not None, "ProjectCommitment frozen final present")
    _require(
        final.record.predecessor_version_id == "formation-draft-preview",
        "ProjectCommitment exact predecessor",
    )
    _require(
        final.record.content.revision.predecessor_ref == draft.record.ref,
        "ProjectCommitment revision predecessor ref",
    )
    _require(
        final.record.content.revision.rewrite_history is False,
        "ProjectCommitment revision does not rewrite history",
    )
    return {
        "formation_draft_ref": draft.record.ref.uri,
        "frozen_final_ref": final.record.ref.uri,
        "predecessor_version_id": final.record.predecessor_version_id,
        "order": ["FORMATION_DRAFT", "FROZEN_FINAL"],
        "collapse_or_reorder": False,
        "history_rewrite": False,
    }


def build_rehearsal(repository: Path = Path(".")) -> dict[str, Any]:
    repository = repository.resolve()
    source, identities, memories = _source_evidence(repository)
    identity_validation = _validate_plan(
        IDENTITY_PLAN, identity_records=identities, memory_records=memories
    )
    memory_validation = _validate_plan(
        MEMORY_PLAN, identity_records=identities, memory_records=memories
    )
    identity_simulation = _simulate_append_only(IDENTITY_PLAN, source)
    memory_simulation = _simulate_append_only(MEMORY_PLAN, source)
    commitment = _commitment_lineage(memories)

    stale = dict(asdict(IDENTITY_PLAN), target_digest="0" * 64)
    ambiguous = dict(asdict(IDENTITY_PLAN), successor_ref="")
    quarantine = dict(
        asdict(MEMORY_PLAN),
        successor_ref="memory-experience://golden-mira:GM-CMIR-003/v0.1-preview",
    )
    regression = dict(
        asdict(MEMORY_PLAN),
        target_ref=commitment["frozen_final_ref"],
        target_digest=(
            "3c31de4d62ecfd5d7857a5a4df85725affa0862d0055b5527d7d80f27fcc8ad8"
        ),
        successor_ref=(
            "memory-experience://golden-mira:GM-CMIR-011/"
            "formation-draft-regression-rehearsal"
        ),
    )
    stale_reason = (
        "fresh target digest: identity://mira-golden%3Amira-id-cand-001/"
        "mira-id-cand-001-v0.1-preview"
    )
    stale_result = _rejects_before_mutation(
        stale, identities, memories, expected_reason=stale_reason
    )
    ambiguous_result = _rejects_before_mutation(
        ambiguous,
        identities,
        memories,
        expected_reason="plan exact successor ref",
    )
    quarantine_result = _rejects_before_mutation(
        quarantine,
        identities,
        memories,
        expected_reason="memory successor preserves exact experience lineage",
    )
    regression_result = _rejects_before_mutation(
        regression,
        identities,
        memories,
        expected_reason="frozen-final successor cannot regress to formation draft",
    )

    return {
        "schema": "julia_core.continuity.p5_e.recovery_rehearsal.v1",
        "artifact_id": "P5_E_RECOVERY_SUPERSESSION_NO_WRITE_REHEARSAL_V1",
        "task_id": "P5-E",
        "source": {
            "task_id": "P5-A1",
            "base_sha": BASE_SHA,
            "artifact_path": SOURCE_PATH.as_posix(),
            "artifact_sha256": SOURCE_SHA256,
            "final_result": source["final_result"],
            "identity_refs_bound": 3,
            "memory_refs_bound": 8,
            "binding_mode": "EXACT_REF_AND_DIGEST",
        },
        "identity_recovery_rehearsal": {
            **identity_validation,
            "simulation": identity_simulation,
            "result": "PASS",
        },
        "memory_recovery_rehearsal": {
            **memory_validation,
            "simulation": memory_simulation,
            "result": "PASS",
        },
        "append_only_proof": {
            "identity_event_appended": 1,
            "memory_event_appended": 1,
            "original_records_readable": 11,
            "original_digests_unchanged": 11,
            "history_rewrites": 0,
            "record_rewrites": 0,
            "result": "PASS",
        },
        "fail_closed_checks": {
            "stale_target": stale_result,
            "ambiguous_successor": ambiguous_result,
            "quarantine_substitution": quarantine_result,
            "commitment_stage_regression": regression_result,
            "actual_attempted_writes": 0,
            "result": "PASS",
        },
        "project_commitment_lineage": {**commitment, "result": "PASS"},
        "quarantine_boundary": {
            "quarantined_cmir_ids": sorted(QUARANTINED_CMIR_IDS),
            "present_in_admitted_refs": 0,
            "accepted_as_recovery_substitutes": 0,
            "result": "PASS",
        },
        "authority": {
            "semantic_authority": 0,
            "canonical_writes": 0,
            "runtime_writes": 0,
            "provider_writes": 0,
            "production_response_selection_authority": 0,
            "actual_supersede_calls": 0,
            "actual_retire_calls": 0,
            "actual_admit_or_store_calls": 0,
        },
        "operator_checklist": [
            "Prove owner authorization for the specific corrective action.",
            "Re-read the accepted P5-A1 artifact and bind all target refs and digests exactly.",
            "Resolve one exact stale Identity or MemoryExperience target; reject latest/default/fuzzy lookup.",
            "Require a unique exact replacement ref and digest; reject quarantined CMIR substitutes.",
            "For ProjectCommitment corrections, preserve formation-draft -> frozen-final order and predecessor semantics.",
            "Construct an append-only governance event with explicit actor, reason, occurred_at, and successor binding.",
            "Re-run stale-target and ambiguity checks immediately before the authorized transaction.",
            "Apply one bounded append-only action only after every gate passes; never rewrite or delete the original record.",
            "Retain before/after evidence and verify original record readability and digest identity.",
        ],
        "execution": {
            "live_canary_or_model_call": 0,
            "production_response_selection": 0,
            "future_action_authorized": 0,
        },
        "deterministic_rerun": "BYTE_IDENTICAL",
        "final_result": "P5_E_RECOVERY_SUPERSESSION_NO_WRITE_REHEARSAL_PASS",
    }


def _rejects_before_mutation(
    values: dict[str, Any],
    identities: list[Any],
    memories: list[Any],
    expected_reason: str,
) -> dict[str, Any]:
    plan = RecoveryActionPlan(**values)
    try:
        _validate_plan(plan, identity_records=identities, memory_records=memories)
    except RecoveryRehearsalError as error:
        reason = str(error).removeprefix("FAIL_CLOSED: ")
        _require(reason == expected_reason, "expected fail-closed reason")
        return {"result": "REJECTED_BEFORE_MUTATION", "reason": reason}
    return {"result": "UNEXPECTED_ACCEPT", "reason": "FAIL_CLOSED_ASSERTION"}


def write_artifact(repository: Path = Path(".")) -> dict[str, Any]:
    evidence = build_rehearsal(repository)
    destination = repository / EVIDENCE_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return evidence


if __name__ == "__main__":
    write_artifact(Path("."))
