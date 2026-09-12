"""Governed exact-version runtime canonical binding repository."""

from __future__ import annotations

import threading
from types import MappingProxyType

from .contracts import (
    GovernedRuntimeCanonicalAuthorityBinding,
    RuntimeCanonicalAuthorityBinding,
    RuntimeCanonicalAuthorityBindingGovernanceEvent,
    RuntimeCanonicalAuthorityBindingRef,
    RuntimeCanonicalAuthorityBindingStatus,
)


class RuntimeCanonicalAuthorityBindingRefNotFoundError(LookupError):
    pass


class RuntimeCanonicalAuthorityBindingConflictError(ValueError):
    pass


class InvalidRuntimeCanonicalAuthorityBindingLifecycleError(ValueError):
    pass


class RuntimeCanonicalAuthorityBindingRepository:
    __slots__ = ("_bindings", "_events", "_lock")

    def __init__(self) -> None:
        object.__setattr__(self, "_bindings", MappingProxyType({}))
        object.__setattr__(self, "_events", MappingProxyType({}))
        object.__setattr__(self, "_lock", threading.RLock())

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("runtime binding repository fields are immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("runtime binding repository fields are immutable")

    def store_candidate(
        self, binding: RuntimeCanonicalAuthorityBinding
    ) -> GovernedRuntimeCanonicalAuthorityBinding:
        if type(binding) is not RuntimeCanonicalAuthorityBinding:
            raise TypeError("store_candidate accepts an exact runtime binding only")
        with self._lock:
            existing = self._bindings.get(binding.ref)
            if existing is not None:
                if existing.digest() != binding.digest():
                    raise RuntimeCanonicalAuthorityBindingConflictError(
                        f"conflicting runtime binding: {binding.ref.uri}"
                    )
                return self.resolve(binding.ref)
            self._validate_lineage(binding)
            event = RuntimeCanonicalAuthorityBindingGovernanceEvent(
                event_id=(
                    f"runtime-binding-candidate:{binding.binding_id}:"
                    f"{binding.binding_version}"
                ),
                target=binding.ref,
                status=RuntimeCanonicalAuthorityBindingStatus.CANDIDATE,
                actor="runtime_binding_submitter",
                reason="Candidate stored; existence does not establish authority.",
                occurred_at=binding.created_at,
            )
            bindings = dict(self._bindings)
            bindings[binding.ref] = binding
            object.__setattr__(self, "_bindings", MappingProxyType(bindings))
            events = dict(self._events)
            events[binding.ref] = (*events.get(binding.ref, ()), event)
            object.__setattr__(self, "_events", MappingProxyType(events))
            return self.resolve(binding.ref)

    def admit(
        self,
        ref: RuntimeCanonicalAuthorityBindingRef,
        *,
        actor: str,
        reason: str,
        occurred_at: str,
    ) -> GovernedRuntimeCanonicalAuthorityBinding:
        self._transition(
            ref,
            RuntimeCanonicalAuthorityBindingStatus.ADMITTED,
            allowed_from={
                RuntimeCanonicalAuthorityBindingStatus.CANDIDATE,
                RuntimeCanonicalAuthorityBindingStatus.ADMITTED,
            },
            actor=actor,
            reason=reason,
            occurred_at=occurred_at,
        )
        return self.resolve(ref)

    def supersede(
        self,
        ref: RuntimeCanonicalAuthorityBindingRef,
        *,
        actor: str,
        reason: str,
        occurred_at: str,
    ) -> GovernedRuntimeCanonicalAuthorityBinding:
        self._transition(
            ref,
            RuntimeCanonicalAuthorityBindingStatus.SUPERSEDED,
            allowed_from={
                RuntimeCanonicalAuthorityBindingStatus.CANDIDATE,
                RuntimeCanonicalAuthorityBindingStatus.ADMITTED,
            },
            actor=actor,
            reason=reason,
            occurred_at=occurred_at,
        )
        return self.resolve(ref)

    def retire(
        self,
        ref: RuntimeCanonicalAuthorityBindingRef,
        *,
        actor: str,
        reason: str,
        occurred_at: str,
    ) -> GovernedRuntimeCanonicalAuthorityBinding:
        self._transition(
            ref,
            RuntimeCanonicalAuthorityBindingStatus.RETIRED,
            allowed_from={
                RuntimeCanonicalAuthorityBindingStatus.CANDIDATE,
                RuntimeCanonicalAuthorityBindingStatus.ADMITTED,
                RuntimeCanonicalAuthorityBindingStatus.SUPERSEDED,
            },
            actor=actor,
            reason=reason,
            occurred_at=occurred_at,
        )
        return self.resolve(ref)

    def resolve(
        self, ref: RuntimeCanonicalAuthorityBindingRef
    ) -> GovernedRuntimeCanonicalAuthorityBinding:
        if type(ref) is not RuntimeCanonicalAuthorityBindingRef:
            raise TypeError("repository resolution requires an exact binding ref")
        with self._lock:
            binding = self._bindings.get(ref)
            if binding is None:
                raise RuntimeCanonicalAuthorityBindingRefNotFoundError(
                    f"unknown runtime binding ref: {ref.uri}"
                )
            events = self._events[ref]
            return GovernedRuntimeCanonicalAuthorityBinding(
                binding=binding,
                status=events[-1].status,
                governance_events=events,
            )

    def _transition(
        self,
        ref: RuntimeCanonicalAuthorityBindingRef,
        status: RuntimeCanonicalAuthorityBindingStatus,
        *,
        allowed_from: set[RuntimeCanonicalAuthorityBindingStatus],
        actor: str,
        reason: str,
        occurred_at: str,
    ) -> None:
        if type(ref) is not RuntimeCanonicalAuthorityBindingRef:
            raise TypeError("lifecycle transition requires an exact binding ref")
        with self._lock:
            current = self.resolve(ref)
            if current.status not in allowed_from:
                raise InvalidRuntimeCanonicalAuthorityBindingLifecycleError(
                    f"cannot transition {ref.uri} from {current.status.value} "
                    f"to {status.value}"
                )
            event = RuntimeCanonicalAuthorityBindingGovernanceEvent(
                event_id=(
                    f"runtime-binding-{status.value.lower()}:{ref.binding_id}:"
                    f"{ref.binding_version}:{len(self._events[ref])}"
                ),
                target=ref,
                status=status,
                actor=actor,
                reason=reason,
                occurred_at=occurred_at,
            )
            events = dict(self._events)
            events[ref] = (*events[ref], event)
            object.__setattr__(self, "_events", MappingProxyType(events))

    def _validate_lineage(self, binding: RuntimeCanonicalAuthorityBinding) -> None:
        if binding.predecessor_version_id is None:
            return
        predecessor = RuntimeCanonicalAuthorityBindingRef(
            binding.binding_id,
            binding.predecessor_version_id,
        )
        if predecessor not in self._bindings:
            raise RuntimeCanonicalAuthorityBindingRefNotFoundError(
                f"unknown predecessor runtime binding: {predecessor.uri}"
            )


__all__ = [
    "InvalidRuntimeCanonicalAuthorityBindingLifecycleError",
    "RuntimeCanonicalAuthorityBindingConflictError",
    "RuntimeCanonicalAuthorityBindingRefNotFoundError",
    "RuntimeCanonicalAuthorityBindingRepository",
]
