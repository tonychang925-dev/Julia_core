"""Exact-version immutable Identity repository (ENG-07 candidate)."""

from __future__ import annotations

import threading
from types import MappingProxyType

from .contracts import (
    GovernedIdentity,
    IdentityGovernanceEvent,
    IdentityRef,
    IdentityStatus,
    IdentityVersion,
)


class IdentityRefNotFoundError(LookupError):
    pass


class IdentityConflictError(ValueError):
    pass


class InvalidIdentityLifecycleError(ValueError):
    pass


def _capability_guarded(cls):
    class LifecycleCapability:
        __slots__ = ()

    capabilities = {}
    original_init = cls.__dict__["__init__"]

    def authorize(self, capability) -> None:
        expected = capabilities.get(self)
        if type(capability) is not LifecycleCapability or capability is not expected:
            raise PermissionError("exact lifecycle capability is required")

    def initialize(self) -> None:
        original_init(self)
        capabilities[self] = LifecycleCapability()

    setattr(cls, f"_{cls.__name__}__authorize_mutation", authorize)
    setattr(cls, "__init__", initialize)

    for method_name in ("store_candidate", "admit", "supersede", "retire"):
        authorized_name = f"_{cls.__name__}__{method_name}_authorized"
        authorized = cls.__dict__[authorized_name]

        def make_public(method_name, authorized):
            def public(self, *args, **kwargs):
                return authorized(self, *args, capability=capabilities[self], **kwargs)

            public.__name__ = method_name
            public.__qualname__ = f"{cls.__qualname__}.{method_name}"
            return public

        setattr(cls, method_name, make_public(method_name, authorized))

    return cls


@_capability_guarded
class IdentityRepository:
    __slots__ = ("_events", "_lock", "_versions")

    """Thread-safe exact-reference store with an append-only governance ledger.

    The repository is intentionally bounded to in-memory semantics in ENG-07.
    IdentityVersion objects are never altered; admission and supersession are
    represented as immutable governance events.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "_versions", MappingProxyType({}))
        object.__setattr__(
            self,
            "_events",
            MappingProxyType({}),
        )
        object.__setattr__(self, "_lock", threading.RLock())

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("IdentityRepository fields are immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("IdentityRepository fields are immutable")

    def __store_candidate_authorized(
        self, version: IdentityVersion, *, capability
    ) -> GovernedIdentity:
        self.__authorize_mutation(capability)
        if type(version) is not IdentityVersion:
            raise TypeError("store_candidate accepts an exact IdentityVersion only")
        with self._lock:
            existing = self._versions.get(version.ref)
            if existing is not None:
                if existing.digest() != version.digest():
                    raise IdentityConflictError(
                        f"conflicting identity version: {version.ref.uri}"
                    )
                return self.resolve(version.ref)

            self._validate_lineage(version)

            event = IdentityGovernanceEvent(
                event_id=f"identity-candidate:{version.lineage_id}:{version.version_id}",
                target=version.ref,
                status=IdentityStatus.CANDIDATE,
                actor="identity_submitter",
                reason="Candidate stored; existence does not establish canonical authority.",
                occurred_at=version.created_at,
            )
            self.__replace_version(version.ref, version, capability=capability)
            self.__replace_events(version.ref, event, capability=capability)
            return self.resolve(version.ref)

    def __admit_authorized(
        self,
        ref: IdentityRef,
        *,
        actor: str,
        reason: str,
        occurred_at: str,
        capability,
    ) -> GovernedIdentity:
        _require_exact_ref(ref)
        return self.__append_event(
            ref,
            IdentityStatus.ADMITTED,
            actor=actor,
            reason=reason,
            occurred_at=occurred_at,
            allowed_from={IdentityStatus.CANDIDATE, IdentityStatus.ADMITTED},
            event_kind="admission",
            capability=capability,
        )

    def __supersede_authorized(
        self,
        ref: IdentityRef,
        *,
        actor: str,
        reason: str,
        occurred_at: str,
        capability,
    ) -> GovernedIdentity:
        _require_exact_ref(ref)
        return self.__append_event(
            ref,
            IdentityStatus.SUPERSEDED,
            actor=actor,
            reason=reason,
            occurred_at=occurred_at,
            allowed_from={IdentityStatus.CANDIDATE, IdentityStatus.ADMITTED},
            event_kind="supersession",
            capability=capability,
        )

    def __retire_authorized(
        self,
        ref: IdentityRef,
        *,
        actor: str,
        reason: str,
        occurred_at: str,
        capability,
    ) -> GovernedIdentity:
        _require_exact_ref(ref)
        return self.__append_event(
            ref,
            IdentityStatus.RETIRED,
            actor=actor,
            reason=reason,
            occurred_at=occurred_at,
            allowed_from={
                IdentityStatus.CANDIDATE,
                IdentityStatus.ADMITTED,
                IdentityStatus.SUPERSEDED,
            },
            event_kind="retirement",
            capability=capability,
        )

    def resolve(self, ref: IdentityRef) -> GovernedIdentity:
        with self._lock:
            version = self._versions.get(ref)
            if version is None:
                raise IdentityRefNotFoundError(f"unknown identity ref: {ref.uri}")
            events = self._events[ref]
            return GovernedIdentity(
                version=version,
                status=events[-1].status,
                governance_events=events,
            )

    def lineage_versions(self, lineage_id: str) -> tuple[IdentityVersion, ...]:
        with self._lock:
            return tuple(
                self._versions[ref]
                for ref in sorted(
                    self._versions, key=lambda item: (item.version_id, item.lineage_id)
                )
                if ref.lineage_id == lineage_id
            )

    def _validate_lineage(self, version: IdentityVersion) -> None:
        lineage_versions = self.lineage_versions(version.lineage_id)
        if any(
            item.contract.identity_id != version.contract.identity_id
            for item in lineage_versions
        ):
            raise IdentityConflictError(
                f"lineage {version.lineage_id} cannot mix identity objects"
            )
        if version.predecessor_version_id is None:
            return
        predecessor_ref = IdentityRef(
            lineage_id=version.lineage_id,
            version_id=version.predecessor_version_id,
        )
        if predecessor_ref not in self._versions:
            raise IdentityRefNotFoundError(
                f"unknown predecessor identity ref: {predecessor_ref.uri}"
            )

    def __append_event(
        self,
        ref: IdentityRef,
        status: IdentityStatus,
        *,
        actor: str,
        reason: str,
        occurred_at: str,
        allowed_from: set[IdentityStatus],
        event_kind: str,
        capability,
    ) -> GovernedIdentity:
        self.__authorize_mutation(capability)
        _require_exact_ref(ref)
        with self._lock:
            current = self.resolve(ref)
            if current.status not in allowed_from:
                raise InvalidIdentityLifecycleError(
                    f"cannot transition {ref.uri} from {current.status.value} to {status.value}"
                )
            event = IdentityGovernanceEvent(
                event_id=f"identity-{event_kind}:{ref.lineage_id}:{ref.version_id}:{len(self._events[ref])}",
                target=ref,
                status=status,
                actor=actor,
                reason=reason,
                occurred_at=occurred_at,
            )
            self.__replace_events(ref, event, capability=capability)
            return self.resolve(ref)

    def __replace_events(
        self, ref: IdentityRef, event: IdentityGovernanceEvent, *, capability
    ) -> None:
        self.__authorize_mutation(capability)
        events = dict(self._events)
        events[ref] = (*events.get(ref, ()), event)
        object.__setattr__(self, "_events", MappingProxyType(events))

    def __replace_version(
        self, ref: IdentityRef, version: IdentityVersion, *, capability
    ) -> None:
        self.__authorize_mutation(capability)
        versions = dict(self._versions)
        versions[ref] = version
        object.__setattr__(self, "_versions", MappingProxyType(versions))


def _require_exact_ref(ref: IdentityRef) -> None:
    if type(ref) is not IdentityRef:
        raise TypeError(
            "identity lifecycle transitions accept exact IdentityRef objects only"
        )


__all__ = [
    "IdentityConflictError",
    "IdentityRefNotFoundError",
    "IdentityRepository",
    "InvalidIdentityLifecycleError",
]
