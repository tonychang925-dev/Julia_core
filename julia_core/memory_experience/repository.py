"""Exact-version immutable MemoryExperience repository."""
from __future__ import annotations

import threading
from collections import defaultdict

from .contracts import (
    CommitmentStage,
    GovernedMemoryExperience,
    MemoryExperienceAdmission,
    MemoryExperienceCandidate,
    MemoryExperienceConflictError,
    MemoryExperienceLifecycleError,
    MemoryExperienceRecord,
    MemoryExperienceRefNotFoundError,
    MemoryExperienceRef,
    MemoryExperienceStatus,
    MemoryExperienceType,
)


class MemoryExperienceRepository:
    """Store exact canonical records and append governance state separately."""

    def __init__(self) -> None:
        self._records: dict[MemoryExperienceRef, MemoryExperienceRecord] = {}
        self._states: dict[MemoryExperienceRef, MemoryExperienceStatus] = {}
        self._events: dict[
            MemoryExperienceRef,
            list[tuple[MemoryExperienceStatus, MemoryExperienceAdmission | None]],
        ] = defaultdict(list)
        self._lock = threading.RLock()

    def store_candidate(self, candidate: MemoryExperienceCandidate) -> GovernedMemoryExperience:
        if type(candidate) is not MemoryExperienceCandidate:
            raise TypeError("store_candidate accepts an exact MemoryExperienceCandidate only")
        if type(candidate.record) is not MemoryExperienceRecord:
            raise TypeError("MemoryExperienceCandidate requires an exact MemoryExperienceRecord")
        record = candidate.record
        with self._lock:
            existing = self._records.get(record.ref)
            if existing is not None:
                if existing.digest() != record.digest():
                    raise MemoryExperienceConflictError(f"conflicting MemoryExperience version: {record.ref.uri}")
                return self.resolve(record.ref)

            self._validate_lineage(record)
            self._records[record.ref] = record
            self._states[record.ref] = MemoryExperienceStatus.CANDIDATE
            self._events[record.ref].append((MemoryExperienceStatus.CANDIDATE, None))
            return self.resolve(record.ref)

    def admit(
        self,
        ref: MemoryExperienceRef,
        *,
        actor: str,
        reason: str,
        occurred_at: str,
    ) -> GovernedMemoryExperience:
        _require_exact_ref(ref)
        with self._lock:
            current = self.resolve(ref)
            if current.status is not MemoryExperienceStatus.CANDIDATE:
                raise MemoryExperienceLifecycleError(
                    f"cannot admit {ref.uri} from {current.status.value}"
                )
            admission = MemoryExperienceAdmission(
                admission_id=f"memory-experience-admission:{ref.experience_id}:{ref.version_id}",
                target=ref,
                actor=actor,
                reason=reason,
                occurred_at=occurred_at,
            )
            self._states[ref] = MemoryExperienceStatus.ADMITTED
            self._events[ref].append((MemoryExperienceStatus.ADMITTED, admission))
            return self.resolve(ref)

    def supersede(
        self,
        ref: MemoryExperienceRef,
        *,
        actor: str,
        reason: str,
        occurred_at: str,
    ) -> GovernedMemoryExperience:
        _require_exact_ref(ref)
        return self._transition(
            ref,
            MemoryExperienceStatus.SUPERSEDED,
            allowed_from={MemoryExperienceStatus.CANDIDATE, MemoryExperienceStatus.ADMITTED},
            actor=actor,
            reason=reason,
            occurred_at=occurred_at,
        )

    def retire(
        self,
        ref: MemoryExperienceRef,
        *,
        actor: str,
        reason: str,
        occurred_at: str,
    ) -> GovernedMemoryExperience:
        _require_exact_ref(ref)
        return self._transition(
            ref,
            MemoryExperienceStatus.RETIRED,
            allowed_from={
                MemoryExperienceStatus.CANDIDATE,
                MemoryExperienceStatus.ADMITTED,
                MemoryExperienceStatus.SUPERSEDED,
            },
            actor=actor,
            reason=reason,
            occurred_at=occurred_at,
        )

    def resolve(self, ref: MemoryExperienceRef) -> GovernedMemoryExperience:
        with self._lock:
            record = self._records.get(ref)
            if record is None:
                raise MemoryExperienceRefNotFoundError(f"unknown MemoryExperience ref: {ref.uri}")
            return GovernedMemoryExperience(
                record=record,
                status=self._states[ref],
                governance_events=tuple(self._events[ref]),
            )

    def experience_versions(self, experience_id: str) -> tuple[MemoryExperienceRecord, ...]:
        with self._lock:
            return tuple(
                self._records[ref]
                for ref in sorted(self._records, key=lambda item: item.version_id)
                if ref.experience_id == experience_id
            )

    def _validate_lineage(self, record: MemoryExperienceRecord) -> None:
        lineage = self.experience_versions(record.experience_id)
        if any(item.experience_type is not record.experience_type for item in lineage):
            raise MemoryExperienceConflictError(
                f"experience {record.experience_id} cannot change canonical type across versions"
            )
        self._validate_project_commitment_stage(record, lineage)
        if record.predecessor_version_id is None:
            return
        predecessor = MemoryExperienceRef(record.experience_id, record.predecessor_version_id)
        if predecessor not in self._records:
            raise MemoryExperienceRefNotFoundError(
                f"unknown predecessor MemoryExperience ref: {predecessor.uri}"
            )

    def _validate_project_commitment_stage(
        self,
        record: MemoryExperienceRecord,
        lineage: tuple[MemoryExperienceRecord, ...],
    ) -> None:
        content = record.content
        if (
            record.experience_type is not MemoryExperienceType.PROJECT_COMMITMENT
            or getattr(content, "payload_schema_version", "v1") != "v2"
        ):
            return
        if content.commitment_stage is CommitmentStage.FORMATION_DRAFT:
            if record.predecessor_version_id is not None:
                raise MemoryExperienceLifecycleError(
                    "FORMATION_DRAFT must be the exact initial commitment stage"
                )
            return
        if record.predecessor_version_id is None or content.revision is None:
            raise MemoryExperienceLifecycleError(
                "FROZEN_FINAL requires an exact predecessor revision"
            )
        expected_predecessor = MemoryExperienceRef(
            record.experience_id, record.predecessor_version_id
        )
        if content.revision.predecessor_ref != expected_predecessor:
            raise MemoryExperienceLifecycleError(
                "commitment revision predecessor must match the record predecessor"
            )
        predecessor = next(
            (
                item
                for item in lineage
                if item.ref == expected_predecessor
            ),
            None,
        )
        if (
            predecessor is None
            or predecessor.content.commitment_stage is not CommitmentStage.FORMATION_DRAFT
        ):
            raise MemoryExperienceRefNotFoundError(
                f"unknown FORMATION_DRAFT predecessor: {expected_predecessor.uri}"
            )

    def _transition(
        self,
        ref: MemoryExperienceRef,
        status: MemoryExperienceStatus,
        *,
        allowed_from: set[MemoryExperienceStatus],
        actor: str,
        reason: str,
        occurred_at: str,
    ) -> GovernedMemoryExperience:
        _require_exact_ref(ref)
        with self._lock:
            current = self.resolve(ref)
            if current.status not in allowed_from:
                raise MemoryExperienceLifecycleError(
                    f"cannot transition {ref.uri} from {current.status.value} to {status.value}"
                )
            admission = MemoryExperienceAdmission(
                admission_id=f"memory-experience-{status.value.lower()}:{ref.experience_id}:{ref.version_id}",
                target=ref,
                actor=actor,
                reason=reason,
                occurred_at=occurred_at,
            )
            self._states[ref] = status
            self._events[ref].append((status, admission))
            return self.resolve(ref)


def _require_exact_ref(ref: MemoryExperienceRef) -> None:
    if type(ref) is not MemoryExperienceRef:
        raise TypeError(
            "MemoryExperience lifecycle transitions accept exact MemoryExperienceRef objects only"
        )


__all__ = ["MemoryExperienceRepository"]
