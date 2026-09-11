"""Exact-version immutable MemoryExperience repository."""

from __future__ import annotations

import threading
from types import MappingProxyType

from .contracts import (
    GovernedMemoryExperience,
    MemoryExperienceAdmission,
    MemoryExperienceCandidate,
    MemoryExperienceConflictError,
    MemoryExperienceLifecycleError,
    MemoryExperienceRecord,
    MemoryExperienceRefNotFoundError,
    MemoryExperienceRef,
    MemoryExperienceStatus,
)


class MemoryExperienceRepository:
    __slots__ = ("_events", "_lock", "_records", "_states")

    """Store exact canonical records and append governance state separately."""

    def __init__(self) -> None:
        object.__setattr__(self, "_records", MappingProxyType({}))
        object.__setattr__(self, "_states", MappingProxyType({}))
        object.__setattr__(self, "_events", MappingProxyType({}))
        object.__setattr__(self, "_lock", threading.RLock())

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("MemoryExperienceRepository fields are immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("MemoryExperienceRepository fields are immutable")

    def store_candidate(
        self, candidate: MemoryExperienceCandidate
    ) -> GovernedMemoryExperience:
        if type(candidate) is not MemoryExperienceCandidate:
            raise TypeError(
                "store_candidate accepts an exact MemoryExperienceCandidate only"
            )
        if type(candidate.record) is not MemoryExperienceRecord:
            raise TypeError(
                "MemoryExperienceCandidate requires an exact MemoryExperienceRecord"
            )
        record = candidate.record
        with self._lock:
            existing = self._records.get(record.ref)
            if existing is not None:
                if existing.digest() != record.digest():
                    raise MemoryExperienceConflictError(
                        f"conflicting MemoryExperience version: {record.ref.uri}"
                    )
                return self.resolve(record.ref)

            self._validate_lineage(record)
            records = dict(self._records)
            records[record.ref] = record
            object.__setattr__(self, "_records", MappingProxyType(records))
            states = dict(self._states)
            states[record.ref] = MemoryExperienceStatus.CANDIDATE
            object.__setattr__(self, "_states", MappingProxyType(states))
            events = dict(self._events)
            events[record.ref] = (
                *events.get(record.ref, ()),
                (MemoryExperienceStatus.CANDIDATE, None),
            )
            object.__setattr__(self, "_events", MappingProxyType(events))
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
            states = dict(self._states)
            states[ref] = MemoryExperienceStatus.ADMITTED
            object.__setattr__(self, "_states", MappingProxyType(states))
            events = dict(self._events)
            events[ref] = (
                *events.get(ref, ()),
                (MemoryExperienceStatus.ADMITTED, admission),
            )
            object.__setattr__(self, "_events", MappingProxyType(events))
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
        with self._lock:
            current = self.resolve(ref)
            allowed_from = {
                MemoryExperienceStatus.CANDIDATE,
                MemoryExperienceStatus.ADMITTED,
            }
            if current.status not in allowed_from:
                raise MemoryExperienceLifecycleError(
                    f"cannot transition {ref.uri} from {current.status.value} to superseded"
                )
            admission = MemoryExperienceAdmission(
                admission_id=f"memory-experience-superseded:{ref.experience_id}:{ref.version_id}",
                target=ref,
                actor=actor,
                reason=reason,
                occurred_at=occurred_at,
            )
            states = dict(self._states)
            states[ref] = MemoryExperienceStatus.SUPERSEDED
            object.__setattr__(self, "_states", MappingProxyType(states))
            events = dict(self._events)
            events[ref] = (
                *events.get(ref, ()),
                (MemoryExperienceStatus.SUPERSEDED, admission),
            )
            object.__setattr__(self, "_events", MappingProxyType(events))
            return self.resolve(ref)

    def retire(
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
            allowed_from = {
                MemoryExperienceStatus.CANDIDATE,
                MemoryExperienceStatus.ADMITTED,
                MemoryExperienceStatus.SUPERSEDED,
            }
            if current.status not in allowed_from:
                raise MemoryExperienceLifecycleError(
                    f"cannot transition {ref.uri} from {current.status.value} to retired"
                )
            admission = MemoryExperienceAdmission(
                admission_id=f"memory-experience-retired:{ref.experience_id}:{ref.version_id}",
                target=ref,
                actor=actor,
                reason=reason,
                occurred_at=occurred_at,
            )
            states = dict(self._states)
            states[ref] = MemoryExperienceStatus.RETIRED
            object.__setattr__(self, "_states", MappingProxyType(states))
            events = dict(self._events)
            events[ref] = (
                *events.get(ref, ()),
                (MemoryExperienceStatus.RETIRED, admission),
            )
            object.__setattr__(self, "_events", MappingProxyType(events))
            return self.resolve(ref)

    def resolve(self, ref: MemoryExperienceRef) -> GovernedMemoryExperience:
        with self._lock:
            record = self._records.get(ref)
            if record is None:
                raise MemoryExperienceRefNotFoundError(
                    f"unknown MemoryExperience ref: {ref.uri}"
                )
            return GovernedMemoryExperience(
                record=record,
                status=self._states[ref],
                governance_events=self._events[ref],
            )

    def experience_versions(
        self, experience_id: str
    ) -> tuple[MemoryExperienceRecord, ...]:
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
        if record.predecessor_version_id is None:
            return
        predecessor = MemoryExperienceRef(
            record.experience_id, record.predecessor_version_id
        )
        if predecessor not in self._records:
            raise MemoryExperienceRefNotFoundError(
                f"unknown predecessor MemoryExperience ref: {predecessor.uri}"
            )


def _require_exact_ref(ref: MemoryExperienceRef) -> None:
    if type(ref) is not MemoryExperienceRef:
        raise TypeError(
            "MemoryExperience lifecycle transitions accept exact MemoryExperienceRef objects only"
        )


__all__ = ["MemoryExperienceRepository"]
