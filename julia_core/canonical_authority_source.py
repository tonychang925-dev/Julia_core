"""Read-only exact canonical semantic authority source binding."""

from __future__ import annotations

from enum import Enum
from typing import Mapping

from julia_core.identity import (
    IdentityRef,
    IdentityRefNotFoundError,
    IdentityResolver,
    IdentityStatus,
)
from julia_core.memory_experience import (
    MemoryExperienceRef,
    MemoryExperienceRefNotFoundError,
    MemoryExperienceResolver,
    MemoryExperienceStatus,
)
from julia_core.projection import (
    EXPERIENCE_FRAME_SCHEMA_VERSION,
    EXPERIENCE_PROJECTION_POLICY_ID,
    EXPERIENCE_PROJECTION_POLICY_VERSION,
    IDENTITY_FRAME_SCHEMA_VERSION,
    ExperienceFrame,
    ExperienceProjectionPolicy,
    IdentityFrame,
    PERSONA_PROJECTION_POLICY_ID,
    PERSONA_PROJECTION_POLICY_VERSION,
    PersonaProjectionPolicy,
)


class CanonicalSemanticAuthorityErrorCode(str, Enum):
    SOURCE_NOT_BOUND = "SOURCE_NOT_BOUND"
    REF_NOT_FOUND = "REF_NOT_FOUND"
    REF_NOT_ADMITTED = "REF_NOT_ADMITTED"
    REF_RETIRED = "REF_RETIRED"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    PROJECTION_FAILURE = "PROJECTION_FAILURE"
    PROVENANCE_FAILURE = "PROVENANCE_FAILURE"


class CanonicalSemanticAuthoritySourceError(Exception):
    """Exact fail-closed authority-source failure."""

    def __init__(
        self,
        code: CanonicalSemanticAuthorityErrorCode,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        if type(code) is not CanonicalSemanticAuthorityErrorCode:
            raise TypeError("authority source error code is inexact")
        if type(message) is not str or not message:
            raise TypeError("authority source error message is inexact")
        super().__init__(message)
        object.__setattr__(self, "_code", code)
        object.__setattr__(self, "_details", dict(details or {}))

    @property
    def code(self) -> CanonicalSemanticAuthorityErrorCode:
        return self._code

    @property
    def details(self) -> dict[str, object]:
        return dict(self._details)

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("authority source errors are immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("authority source errors are immutable")


class CanonicalSemanticAuthoritySource:
    """Consumer-facing read-only projection binding for governed authority.

    Repository population and admission remain outside this API. A caller binds
    exact resolvers owned by the canonical authority lifecycle; this object only
    resolves, validates, and projects exact admitted references.
    """

    def __init__(
        self,
        *,
        identity_resolver: IdentityResolver | None = None,
        memory_resolver: MemoryExperienceResolver | None = None,
    ) -> None:
        if (
            identity_resolver is not None
            and type(identity_resolver) is not IdentityResolver
        ):
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.TYPE_MISMATCH,
                "identity resolver must be an exact IdentityResolver",
            )
        if (
            memory_resolver is not None
            and type(memory_resolver) is not MemoryExperienceResolver
        ):
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.TYPE_MISMATCH,
                "memory resolver must be an exact MemoryExperienceResolver",
            )
        object.__setattr__(self, "_identity_resolver", identity_resolver)
        object.__setattr__(self, "_memory_resolver", memory_resolver)
        object.__setattr__(self, "_identity_policy", PersonaProjectionPolicy())
        object.__setattr__(self, "_memory_policy", ExperienceProjectionPolicy())

    def resolve_identity_frame(self, ref: IdentityRef) -> IdentityFrame:
        """Resolve and project one exact admitted canonical identity reference."""
        resolver = self._require_identity_resolver()
        if type(ref) is not IdentityRef:
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.TYPE_MISMATCH,
                "identity lookup requires an exact IdentityRef",
                details={"received_type": type(ref).__name__},
            )
        try:
            governed = resolver.resolve(ref)
        except IdentityRefNotFoundError as error:
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.REF_NOT_FOUND,
                f"exact identity reference is not present: {ref.uri}",
            ) from error
        self._require_admitted(
            governed.status,
            IdentityStatus.RETIRED,
            IdentityStatus.ADMITTED,
            "identity",
            ref.uri,
        )
        try:
            frame = self._identity_policy.project_ref(ref, resolver)
        except Exception as error:
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.PROJECTION_FAILURE,
                f"canonical identity projection failed: {type(error).__name__}",
            ) from error
        expected_provenance = tuple(
            item.to_dict() for item in governed.version.provenance_refs
        )
        if (
            type(frame) is not IdentityFrame
            or frame.source_ref != ref
            or frame.source_status is not IdentityStatus.ADMITTED
            or frame.source_digest != governed.version.digest()
            or frame.identity_id != governed.version.contract.identity_id
            or frame.predecessor_version_id != governed.version.predecessor_version_id
            or not frame.provenance_refs
            or tuple(frame.provenance_refs) != expected_provenance
            or frame.schema_version != IDENTITY_FRAME_SCHEMA_VERSION
            or frame.policy_id != PERSONA_PROJECTION_POLICY_ID
            or frame.policy_version != PERSONA_PROJECTION_POLICY_VERSION
        ):
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.PROVENANCE_FAILURE,
                "projected identity frame does not preserve canonical provenance",
                details={"source_ref": ref.uri},
            )
        return frame

    def resolve_experience_frame(self, ref: MemoryExperienceRef) -> ExperienceFrame:
        """Resolve and project one exact admitted canonical experience reference."""
        resolver = self._require_memory_resolver()
        if type(ref) is not MemoryExperienceRef:
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.TYPE_MISMATCH,
                "experience lookup requires an exact MemoryExperienceRef",
                details={"received_type": type(ref).__name__},
            )
        try:
            governed = resolver.resolve(ref)
        except MemoryExperienceRefNotFoundError as error:
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.REF_NOT_FOUND,
                f"exact experience reference is not present: {ref.uri}",
            ) from error
        self._require_admitted(
            governed.status,
            MemoryExperienceStatus.RETIRED,
            MemoryExperienceStatus.ADMITTED,
            "experience",
            ref.uri,
        )
        try:
            frame = self._memory_policy.project_ref(ref, resolver)
        except Exception as error:
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.PROJECTION_FAILURE,
                f"canonical experience projection failed: {type(error).__name__}",
            ) from error
        expected_provenance = tuple(
            item.to_dict() for item in governed.record.provenance_refs
        )
        if (
            type(frame) is not ExperienceFrame
            or frame.source_ref != ref
            or frame.source_status is not MemoryExperienceStatus.ADMITTED
            or frame.source_digest != governed.record.digest()
            or frame.experience_id != governed.record.experience_id
            or frame.version_id != governed.record.version_id
            or frame.predecessor_version_id != governed.record.predecessor_version_id
            or frame.experience_type is not governed.record.experience_type
            or frame.created_at != governed.record.created_at
            or not frame.provenance_refs
            or tuple(frame.provenance_refs) != expected_provenance
            or frame.schema_version != EXPERIENCE_FRAME_SCHEMA_VERSION
            or frame.policy_id != EXPERIENCE_PROJECTION_POLICY_ID
            or frame.policy_version != EXPERIENCE_PROJECTION_POLICY_VERSION
        ):
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.PROVENANCE_FAILURE,
                "projected experience frame does not preserve canonical provenance",
                details={"source_ref": ref.uri},
            )
        return frame

    def _require_identity_resolver(self) -> IdentityResolver:
        resolver = self._identity_resolver
        if resolver is None:
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.SOURCE_NOT_BOUND,
                "canonical identity authority source is not bound",
            )
        return resolver

    def _require_memory_resolver(self) -> MemoryExperienceResolver:
        resolver = self._memory_resolver
        if resolver is None:
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.SOURCE_NOT_BOUND,
                "canonical experience authority source is not bound",
            )
        return resolver

    @staticmethod
    def _require_admitted(
        status: object,
        retired_status: object,
        admitted_status: object,
        authority_name: str,
        source_ref: str,
    ) -> None:
        if status is retired_status:
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.REF_RETIRED,
                f"canonical {authority_name} reference is retired: {source_ref}",
            )
        if status is not admitted_status:
            raise CanonicalSemanticAuthoritySourceError(
                CanonicalSemanticAuthorityErrorCode.REF_NOT_ADMITTED,
                f"canonical {authority_name} reference is not admitted: {source_ref}",
            )

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("canonical authority source bindings are immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("canonical authority source bindings are immutable")


__all__ = [
    "CanonicalSemanticAuthorityErrorCode",
    "CanonicalSemanticAuthoritySource",
    "CanonicalSemanticAuthoritySourceError",
]
