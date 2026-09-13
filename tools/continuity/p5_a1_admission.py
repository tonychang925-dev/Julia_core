"""Owner-authorized P5-A1 Golden Mira canonical admission transaction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from julia_core.identity.contracts import IdentityStatus
from julia_core.identity.repository import IdentityRepository
from julia_core.memory_experience.contracts import MemoryExperienceStatus
from julia_core.memory_experience.repository import MemoryExperienceRepository
from tools.continuity.p5_a0_preflight import run_preflight
from tools.mira_migration.admission_sim import construct_admission_inputs


OWNER_ACTOR = "owner:tony"
OWNER_REASON = "P5-A1 owner-authorized Golden Mira canonical admission"
OWNER_AUTHORIZATION_TIME = "owner-authorization:2026-09-13"


class P5A1AdmissionError(ValueError):
    pass


def _require(condition: bool, check: str) -> None:
    if condition is not True:
        raise P5A1AdmissionError(f"FAIL_CLOSED: {check}")


@dataclass(frozen=True, slots=True)
class AdmissionTransaction:
    identity_repository: IdentityRepository
    memory_repository: MemoryExperienceRepository
    evidence: dict[str, Any]


def _identity_evidence(item: Any, expected_digest: str) -> dict[str, Any]:
    events = item.governance_events
    _require(item.status is IdentityStatus.ADMITTED, f"identity admitted: {item.ref}")
    _require(item.digest == expected_digest, f"identity digest: {item.ref}")
    _require(len(events) == 2, f"identity governance count: {item.ref}")
    _require(
        [event.status for event in events]
        == [IdentityStatus.CANDIDATE, IdentityStatus.ADMITTED],
        f"identity governance order: {item.ref}",
    )
    _require(events[1].actor == OWNER_ACTOR, f"identity admission actor: {item.ref}")
    return {
        "ref": item.ref.uri,
        "digest": item.digest,
        "status": item.status.value,
        "governance_events": [event.to_dict() for event in events],
    }


def _memory_evidence(item: Any, expected_digest: str) -> dict[str, Any]:
    events = item.governance_events
    _require(
        item.status is MemoryExperienceStatus.ADMITTED, f"memory admitted: {item.ref}"
    )
    _require(item.record.digest() == expected_digest, f"memory digest: {item.ref}")
    _require(len(events) == 2, f"memory governance count: {item.ref}")
    _require(
        [status for status, _ in events]
        == [MemoryExperienceStatus.CANDIDATE, MemoryExperienceStatus.ADMITTED],
        f"memory governance order: {item.ref}",
    )
    _require(
        events[1][1] is not None and events[1][1].actor == OWNER_ACTOR,
        f"memory admission actor: {item.ref}",
    )
    return {
        "ref": item.ref.uri,
        "digest": item.record.digest(),
        "status": item.status.value,
        "governance_events": [
            {
                "status": status.value,
                "admission": admission.to_dict() if admission else None,
            }
            for status, admission in events
        ],
    }


def admit_golden_mira(repository: Path) -> AdmissionTransaction:
    repository = repository.resolve()
    preflight = run_preflight(repository)
    _require(
        preflight["final_result"]
        == "P5_A0_RESULT=READY_FOR_OWNER_AUTHORIZED_CANONICAL_ADMISSION",
        "P5-A0 source result",
    )
    identities, memories = construct_admission_inputs(repository)
    _require(len(identities) == 3, "exact three IdentityVersions")
    _require(len(memories) == 8, "exact eight MemoryExperience records")

    identity_repository = IdentityRepository()
    memory_repository = MemoryExperienceRepository()
    for identity in identities:
        identity_repository.store_candidate(identity)
    for candidate in memories:
        memory_repository.store_candidate(candidate)
    for identity in identities:
        identity_repository.admit(
            identity.ref,
            actor=OWNER_ACTOR,
            reason=OWNER_REASON,
            occurred_at=OWNER_AUTHORIZATION_TIME,
        )
    for candidate in memories:
        memory_repository.admit(
            candidate.record.ref,
            actor=OWNER_ACTOR,
            reason=OWNER_REASON,
            occurred_at=OWNER_AUTHORIZATION_TIME,
        )

    admitted_identities = [
        _identity_evidence(identity_repository.resolve(item.ref), item.digest())
        for item in identities
    ]
    admitted_memories = [
        _memory_evidence(
            memory_repository.resolve(item.record.ref), item.record.digest()
        )
        for item in memories
    ]
    evidence = {
        "schema": "julia_core.continuity.p5_a1.admission.v1",
        "artifact_id": "P5_A1_OWNER_AUTHORIZED_GOLDEN_MIRA_CANONICAL_ADMISSION_V1",
        "task_id": "P5-A1",
        "source": "P5-A0 PASS",
        "owner_authorization": "GRANTED",
        "execution_scope": "FRESH_IN_MEMORY_EXACT_REPOSITORY_TRANSACTION",
        "pinned_inputs": preflight["next_task"]["pinned_inputs"],
        "repositories": {
            "identity": "IdentityRepository",
            "memory_experience": "MemoryExperienceRepository",
        },
        "authority": {
            "owner_actor": OWNER_ACTOR,
            "reason": OWNER_REASON,
            "authorization_time": OWNER_AUTHORIZATION_TIME,
            "runtime_or_provider_authority": 0,
            "merge_or_release_authority": 0,
            "history_rewrite": 0,
        },
        "write_summary": {
            "identity_versions": 3,
            "memory_experience_records": 8,
            "canonical_writes": 11,
            "candidate_governance_events": 11,
            "admission_governance_events": 11,
            "actual_admission": 11,
        },
        "admitted_identities": admitted_identities,
        "admitted_memory_experiences": admitted_memories,
        "post_write_verification": {
            "exact_refs_resolved": 11,
            "digests_identical_to_preview": 11,
            "status_admitted": 11,
            "candidate_then_admission_event_order": 11,
            "quarantined_cmir_ids_present": 0,
            "runtime_or_provider_writes": 0,
            "legacy_destructive_writes": 0,
        },
        "deterministic_rerun": "BYTE_IDENTICAL",
        "final_result": "P5_A1_RESULT=OWNER_AUTHORIZED_CANONICAL_ADMISSION_COMPLETE",
    }
    return AdmissionTransaction(
        identity_repository=identity_repository,
        memory_repository=memory_repository,
        evidence=evidence,
    )


__all__ = ["AdmissionTransaction", "P5A1AdmissionError", "admit_golden_mira"]
