"""Exact Continuity C-06 recovery hydration seam.

Hydration resolves checkpoint pointers into non-authoritative projection
frames. It does not admit context, render model input, mutate canonical
repositories, or establish a second persona authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any
from urllib.parse import quote, unquote, urlsplit

from julia_core.identity import (
    GovernedIdentity,
    IdentityRefNotFoundError,
    IdentityRef,
    IdentityResolver,
    IdentityStatus,
)
from julia_core.memory_experience import (
    GovernedMemoryExperience,
    MemoryExperienceRefNotFoundError,
    MemoryExperienceRef,
    MemoryExperienceResolver,
    MemoryExperienceStatus,
)
from julia_core.projection import (
    ExperienceFrame,
    ExperienceProjectionPolicy,
    IdentityFrame,
    PersonaProjectionPolicy,
)

from .contracts import ContinuityCheckpoint


CONTINUITY_HYDRATION_POLICY_ID = "continuity.hydration.exact_refs"
CONTINUITY_HYDRATION_POLICY_VERSION = "1.0.0"
CONTINUITY_RECOVERY_PACKAGE_SCHEMA_VERSION = "1.0.0"


class ContinuityHydrationError(RuntimeError):
    """Fail-closed hydration result with no partial-success package."""

    def __init__(self, failure_manifest: dict[str, Any]) -> None:
        super().__init__(failure_manifest.get("message", "continuity hydration failed"))
        self.failure_manifest = MappingProxyType(dict(failure_manifest))


@dataclass(frozen=True, slots=True)
class ContinuityHydrationOutcome:
    source_kind: str
    source_ref: IdentityRef | MemoryExperienceRef
    source_digest: str
    source_status: IdentityStatus | MemoryExperienceStatus
    projection_policy_id: str
    projection_policy_version: str
    frame_digest: str
    hydration_policy_id: str
    hydration_policy_version: str

    def __post_init__(self) -> None:
        if self.source_kind not in ("identity", "memory_experience"):
            raise TypeError("invalid hydration outcome source kind")
        if type(self.source_digest) is not str or not self.source_digest:
            raise TypeError("hydration outcome requires a source digest")
        if type(self.frame_digest) is not str or not self.frame_digest:
            raise TypeError("hydration outcome requires a frame digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "source_ref": self.source_ref.to_dict(),
            "source_digest": self.source_digest,
            "source_status": self.source_status.value,
            "projection": {
                "policy_id": self.projection_policy_id,
                "policy_version": self.projection_policy_version,
                "frame_digest": self.frame_digest,
            },
            "hydration_policy_id": self.hydration_policy_id,
            "hydration_policy_version": self.hydration_policy_version,
        }


@dataclass(frozen=True, slots=True)
class ContinuityRecoveryPackage:
    schema_version: str
    hydration_policy_id: str
    hydration_policy_version: str
    checkpoint_id: str
    recovery_reason: str
    identity_frames: tuple[IdentityFrame, ...]
    experience_frames: tuple[ExperienceFrame, ...]
    outcomes: tuple[ContinuityHydrationOutcome, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "identity_frames", tuple(self.identity_frames))
        object.__setattr__(self, "experience_frames", tuple(self.experience_frames))
        object.__setattr__(self, "outcomes", tuple(self.outcomes))
        if any(type(frame) is not IdentityFrame for frame in self.identity_frames):
            raise TypeError("identity_frames requires exact IdentityFrame values")
        if any(type(frame) is not ExperienceFrame for frame in self.experience_frames):
            raise TypeError("experience_frames requires exact ExperienceFrame values")
        if any(
            type(outcome) is not ContinuityHydrationOutcome for outcome in self.outcomes
        ):
            raise TypeError("outcomes requires exact ContinuityHydrationOutcome values")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.continuity.recovery_package.v1",
            "schema_version": self.schema_version,
            "hydration_policy": {
                "policy_id": self.hydration_policy_id,
                "policy_version": self.hydration_policy_version,
            },
            "checkpoint_id": self.checkpoint_id,
            "recovery_reason": self.recovery_reason,
            "identity_frames": [frame.to_dict() for frame in self.identity_frames],
            "experience_frames": [frame.to_dict() for frame in self.experience_frames],
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
            "authority": {
                "identity_canonical_authority": "IdentityVersion",
                "memory_canonical_authority": "MemoryExperienceRecord",
                "projection_authoritative": False,
                "package_authoritative": False,
                "model_visibility_decided": False,
                "context_admission_authority": False,
                "retrieval_authority": False,
                "consent_authority": False,
                "runtime_authority": False,
            },
        }

    def canonical_serialization(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def digest(self) -> str:
        return hashlib.sha256(
            self.canonical_serialization().encode("utf-8")
        ).hexdigest()


def hydrate_continuity_checkpoint(
    checkpoint: ContinuityCheckpoint,
    *,
    identity_resolver: IdentityResolver,
    memory_resolver: MemoryExperienceResolver,
    recovery_reason: str,
) -> ContinuityRecoveryPackage:
    """Hydrate exact checkpoint refs into an immutable internal package."""
    if type(checkpoint) is not ContinuityCheckpoint:
        raise TypeError("hydration accepts an exact ContinuityCheckpoint only")
    if type(identity_resolver) is not IdentityResolver:
        raise TypeError("hydration accepts an exact IdentityResolver only")
    if type(memory_resolver) is not MemoryExperienceResolver:
        raise TypeError("hydration accepts an exact MemoryExperienceResolver only")
    if type(recovery_reason) is not str or not recovery_reason.strip():
        raise TypeError("recovery_reason must be a non-empty exact built-in string")
    if type(checkpoint.checkpoint_id) is not str or not checkpoint.checkpoint_id:
        raise ContinuityHydrationError(
            _failure(
                checkpoint,
                "invalid_checkpoint",
                "checkpoint_id must be a non-empty exact built-in string",
            )
        )

    identity_refs = tuple(
        _parse_ref(checkpoint, ref, "identity", IdentityRef, "lineage_id")
        for ref in _snapshot_refs(checkpoint, checkpoint.identity_refs, "identity_refs")
    )
    memory_refs = tuple(
        _parse_ref(
            checkpoint, ref, "memory-experience", MemoryExperienceRef, "experience_id"
        )
        for ref in _snapshot_refs(
            checkpoint, checkpoint.protected_memory_refs, "protected_memory_refs"
        )
    )
    _require_unique(checkpoint, identity_refs, "identity_refs")
    _require_unique(checkpoint, memory_refs, "protected_memory_refs")

    identity_policy = PersonaProjectionPolicy()
    memory_policy = ExperienceProjectionPolicy()
    identity_frames: list[IdentityFrame] = []
    memory_frames: list[ExperienceFrame] = []
    outcomes: list[ContinuityHydrationOutcome] = []

    try:
        for ref in identity_refs:
            try:
                governed = identity_resolver.resolve(ref)
            except IdentityRefNotFoundError as error:
                raise ContinuityHydrationError(
                    {
                        **_failure(
                            checkpoint,
                            "unknown_exact_ref",
                            "exact IdentityRef is not present in the canonical repository",
                        ),
                        "source_ref": ref.uri,
                    }
                ) from error
            frame = identity_policy.project_ref(ref, identity_resolver)
            _validate_identity_projection(ref, governed, frame)
            _require_admitted(frame.source_status, checkpoint, ref.uri)
            identity_frames.append(frame)
            outcomes.append(
                ContinuityHydrationOutcome(
                    source_kind="identity",
                    source_ref=ref,
                    source_digest=frame.source_digest,
                    source_status=frame.source_status,
                    projection_policy_id=identity_policy.policy_id,
                    projection_policy_version=identity_policy.policy_version,
                    frame_digest=frame.digest(),
                    hydration_policy_id=CONTINUITY_HYDRATION_POLICY_ID,
                    hydration_policy_version=CONTINUITY_HYDRATION_POLICY_VERSION,
                )
            )
        for ref in memory_refs:
            try:
                governed = memory_resolver.resolve(ref)
            except MemoryExperienceRefNotFoundError as error:
                raise ContinuityHydrationError(
                    {
                        **_failure(
                            checkpoint,
                            "unknown_exact_ref",
                            "exact MemoryExperienceRef is not present in the canonical repository",
                        ),
                        "source_ref": ref.uri,
                    }
                ) from error
            frame = memory_policy.project_ref(ref, memory_resolver)
            _validate_memory_projection(ref, governed, frame)
            _require_admitted(frame.source_status, checkpoint, ref.uri)
            memory_frames.append(frame)
            outcomes.append(
                ContinuityHydrationOutcome(
                    source_kind="memory_experience",
                    source_ref=ref,
                    source_digest=frame.source_digest,
                    source_status=frame.source_status,
                    projection_policy_id=memory_policy.policy_id,
                    projection_policy_version=memory_policy.policy_version,
                    frame_digest=frame.digest(),
                    hydration_policy_id=CONTINUITY_HYDRATION_POLICY_ID,
                    hydration_policy_version=CONTINUITY_HYDRATION_POLICY_VERSION,
                )
            )
    except ContinuityHydrationError:
        raise
    except Exception as error:
        raise ContinuityHydrationError(
            _failure(
                checkpoint,
                "exact_resolution_failed",
                f"exact canonical resolution failed: {type(error).__name__}",
            )
        ) from error

    return ContinuityRecoveryPackage(
        schema_version=CONTINUITY_RECOVERY_PACKAGE_SCHEMA_VERSION,
        hydration_policy_id=CONTINUITY_HYDRATION_POLICY_ID,
        hydration_policy_version=CONTINUITY_HYDRATION_POLICY_VERSION,
        checkpoint_id=checkpoint.checkpoint_id,
        recovery_reason=recovery_reason,
        identity_frames=tuple(identity_frames),
        experience_frames=tuple(memory_frames),
        outcomes=tuple(outcomes),
    )


def _snapshot_refs(
    checkpoint: ContinuityCheckpoint, values: object, field_name: str
) -> tuple[str, ...]:
    if type(values) is not list:
        raise ContinuityHydrationError(
            _failure(
                checkpoint,
                "invalid_checkpoint_field",
                f"{field_name} must be an exact checkpoint list",
            )
        )
    snapshot = tuple(values)
    if any(type(ref) is not str for ref in snapshot):
        raise ContinuityHydrationError(
            _failure(
                checkpoint,
                "invalid_ref_type",
                f"{field_name} requires exact built-in strings",
            )
        )
    return snapshot


def _parse_ref(
    checkpoint: ContinuityCheckpoint,
    value: str,
    scheme: str,
    ref_type: type,
    authority_field: str,
) -> IdentityRef | MemoryExperienceRef:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise ContinuityHydrationError(
            _ref_failure(
                checkpoint, "malformed_ref", "checkpoint ref is not a valid URI", value
            )
        ) from error
    if (
        parsed.scheme != scheme
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ContinuityHydrationError(
            _ref_failure(
                checkpoint,
                "unsupported_ref",
                "checkpoint ref has an unsupported scheme or URI component",
                value,
            )
        )
    path_parts = parsed.path.split("/")
    if len(path_parts) != 2 or not path_parts[1] or parsed.path != f"/{path_parts[1]}":
        raise ContinuityHydrationError(
            _ref_failure(
                checkpoint,
                "malformed_ref",
                "checkpoint ref must contain exactly authority and version segments",
                value,
            )
        )
    authority = parsed.netloc
    version_id = path_parts[1]
    try:
        if scheme == "identity":
            decoded_authority = unquote(authority, errors="strict")
            decoded_version = unquote(version_id, errors="strict")
            if (
                quote(decoded_authority, safe="") != authority
                or quote(decoded_version, safe="") != version_id
            ):
                raise ValueError("non-canonical percent encoding")
        else:
            decoded_authority = authority
            decoded_version = version_id
            if "%" in authority or "%" in version_id:
                raise ValueError("non-canonical percent encoding")
        ref = ref_type(
            **{authority_field: decoded_authority, "version_id": decoded_version}
        )
    except (TypeError, ValueError) as error:
        raise ContinuityHydrationError(
            _ref_failure(
                checkpoint,
                "malformed_ref",
                "checkpoint ref contains invalid IDs",
                value,
            )
        ) from error
    if type(ref) is not ref_type or ref.uri != value:
        raise ContinuityHydrationError(
            _ref_failure(
                checkpoint,
                "non_round_trip_ref",
                "checkpoint ref does not round-trip",
                value,
            )
        )
    return ref


def _require_unique(
    checkpoint: ContinuityCheckpoint,
    refs: tuple[IdentityRef | MemoryExperienceRef, ...],
    field_name: str,
) -> None:
    if len(refs) != len(set(refs)):
        raise ContinuityHydrationError(
            _failure(
                checkpoint,
                "ambiguous_ref",
                f"{field_name} contains duplicate refs",
            )
        )


def _validate_identity_projection(
    ref: IdentityRef, governed: GovernedIdentity, frame: IdentityFrame
) -> None:
    if type(governed) is not GovernedIdentity or type(frame) is not IdentityFrame:
        raise TypeError("identity canonical projection returned an invalid exact type")
    if (
        governed.ref != ref
        or frame.source_ref != ref
        or frame.source_digest != governed.version.digest()
        or frame.source_status != governed.status
        or frame.provenance_refs
        != tuple(item.to_dict() for item in governed.version.provenance_refs)
    ):
        raise ValueError("identity projection does not match its canonical source")


def _validate_memory_projection(
    ref: MemoryExperienceRef,
    governed: GovernedMemoryExperience,
    frame: ExperienceFrame,
) -> None:
    if (
        type(governed) is not GovernedMemoryExperience
        or type(frame) is not ExperienceFrame
    ):
        raise TypeError("memory canonical projection returned an invalid exact type")
    if (
        governed.record.ref != ref
        or frame.source_ref != ref
        or frame.source_digest != governed.record.digest()
        or frame.source_status != governed.status
        or frame.experience_id != governed.record.experience_id
        or frame.version_id != governed.record.version_id
        or frame.experience_type != governed.record.experience_type
        or frame.content != governed.record.content.to_dict()
        or frame.provenance_refs
        != tuple(item.to_dict() for item in governed.record.provenance_refs)
    ):
        raise ValueError("memory projection does not match its canonical source")


def _require_admitted(
    status: IdentityStatus | MemoryExperienceStatus,
    checkpoint: ContinuityCheckpoint,
    ref_uri: str,
) -> None:
    if status.value != "ADMITTED":
        raise ContinuityHydrationError(
            {
                **_failure(
                    checkpoint,
                    "non_admitted_source",
                    f"exact source is {status.value}, not ADMITTED",
                ),
                "source_ref": ref_uri,
                "source_status": status.value,
            }
        )


def _failure(
    checkpoint: ContinuityCheckpoint | None, code: str, message: str
) -> dict[str, Any]:
    return {
        "schema": "julia_core.continuity.hydration_failure.v1",
        "code": code,
        "message": message,
        "checkpoint_id": checkpoint.checkpoint_id if checkpoint is not None else None,
        "partial_success": False,
    }


def _ref_failure(
    checkpoint: ContinuityCheckpoint, code: str, message: str, ref: str
) -> dict[str, Any]:
    return {
        **_failure(checkpoint, code, message),
        "source_ref": ref,
    }


__all__ = [
    "CONTINUITY_HYDRATION_POLICY_ID",
    "CONTINUITY_HYDRATION_POLICY_VERSION",
    "CONTINUITY_RECOVERY_PACKAGE_SCHEMA_VERSION",
    "ContinuityHydrationError",
    "ContinuityHydrationOutcome",
    "ContinuityRecoveryPackage",
    "hydrate_continuity_checkpoint",
]
