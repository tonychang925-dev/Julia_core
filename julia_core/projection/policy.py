"""Deterministic Identity-only PersonaProjection policy."""
from __future__ import annotations

from julia_core.identity import IdentityRef, IdentityResolver
from julia_core.memory_experience import (
    GovernedMemoryExperience,
    MemoryExperienceRef,
    MemoryExperienceResolver,
)

from .contracts import (
    EXPERIENCE_FRAME_SCHEMA_VERSION,
    EXPERIENCE_PROJECTION_POLICY_ID,
    EXPERIENCE_PROJECTION_POLICY_VERSION,
    IDENTITY_FRAME_SCHEMA_VERSION,
    ExperienceFrame,
    PERSONA_PROJECTION_POLICY_ID,
    PERSONA_PROJECTION_POLICY_VERSION,
    IdentityFrame,
)


class PersonaProjectionPolicy:
    """Project governed Identity semantics without semantic transformation."""

    policy_id = PERSONA_PROJECTION_POLICY_ID
    policy_version = PERSONA_PROJECTION_POLICY_VERSION

    def project(self, governed: object) -> IdentityFrame:
        raise TypeError("direct GovernedIdentity projection is forbidden; use project_ref with IdentityResolver")

    def _project(self, governed) -> IdentityFrame:
        version = governed.version
        contract = version.contract
        return IdentityFrame(
            schema_version=IDENTITY_FRAME_SCHEMA_VERSION,
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            source_ref=version.ref,
            source_digest=version.digest(),
            source_status=governed.status,
            identity_id=contract.identity_id,
            predecessor_version_id=version.predecessor_version_id,
            anchors=tuple(item.to_dict() for item in contract.anchors),
            values=tuple(item.to_dict() for item in contract.values),
            boundaries=tuple(item.to_dict() for item in contract.boundaries),
            relationship_role_anchors=tuple(
                item.to_dict() for item in contract.relationship_role_anchors
            ),
            provenance_refs=tuple(item.to_dict() for item in version.provenance_refs),
        )

    def project_ref(self, ref: IdentityRef, resolver: IdentityResolver) -> IdentityFrame:
        if type(resolver) is not IdentityResolver:
            raise TypeError("project_ref accepts an exact IdentityResolver only")
        if type(ref) is not IdentityRef:
            raise TypeError("project_ref accepts an exact IdentityRef only")
        return self._project(resolver.resolve(ref))


class ExperienceProjectionPolicy:
    """Project one governed MemoryExperience without semantic transformation."""

    policy_id = EXPERIENCE_PROJECTION_POLICY_ID
    policy_version = EXPERIENCE_PROJECTION_POLICY_VERSION

    def project(self, governed: object) -> ExperienceFrame:
        raise TypeError(
            "direct GovernedMemoryExperience projection is forbidden; use project_ref with MemoryExperienceResolver"
        )

    def project_ref(
        self,
        ref: MemoryExperienceRef,
        resolver: MemoryExperienceResolver,
    ) -> ExperienceFrame:
        if type(resolver) is not MemoryExperienceResolver:
            raise TypeError("project_ref accepts an exact MemoryExperienceResolver only")
        if type(ref) is not MemoryExperienceRef:
            raise TypeError("project_ref accepts an exact MemoryExperienceRef only")
        governed = resolver.resolve(ref)
        if type(governed) is not GovernedMemoryExperience:
            raise TypeError("ExperienceProjectionPolicy requires GovernedMemoryExperience")
        record = governed.record
        return ExperienceFrame(
            schema_version=EXPERIENCE_FRAME_SCHEMA_VERSION,
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            source_ref=record.ref,
            source_digest=record.digest(),
            source_status=governed.status,
            experience_id=record.experience_id,
            version_id=record.version_id,
            predecessor_version_id=record.predecessor_version_id,
            experience_type=record.experience_type,
            content=record.content.to_dict(),
            provenance_refs=tuple(item.to_dict() for item in record.provenance_refs),
            created_at=record.created_at,
        )


__all__ = ["ExperienceProjectionPolicy", "PersonaProjectionPolicy"]
