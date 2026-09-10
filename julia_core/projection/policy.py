"""Deterministic Identity-only PersonaProjection policy."""
from __future__ import annotations

from julia_core.identity import GovernedIdentity, IdentityRef, IdentityResolver

from .contracts import (
    IDENTITY_FRAME_SCHEMA_VERSION,
    PERSONA_PROJECTION_POLICY_ID,
    PERSONA_PROJECTION_POLICY_VERSION,
    IdentityFrame,
)


class PersonaProjectionPolicy:
    """Project governed Identity semantics without semantic transformation."""

    policy_id = PERSONA_PROJECTION_POLICY_ID
    policy_version = PERSONA_PROJECTION_POLICY_VERSION

    def project(self, governed: GovernedIdentity) -> IdentityFrame:
        if not isinstance(governed, GovernedIdentity):
            raise TypeError("PersonaProjectionPolicy accepts GovernedIdentity only")

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
        if not isinstance(resolver, IdentityResolver):
            raise TypeError("project_ref accepts IdentityResolver only")
        return self.project(resolver.resolve(ref))


__all__ = ["PersonaProjectionPolicy"]
