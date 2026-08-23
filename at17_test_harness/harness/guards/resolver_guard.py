"""Resolver boundary guard — AT17-R1-003 / AT17-R1-004.

M8.0 §5.2: the Artifact Resolver validates artifacts. It must NEVER modify
provenance, rewrite lineage, or approve formation.

Forbidden operations (must REJECT):

    update_provenance    → PROVENANCE_AUTHORITY_FORBIDDEN
    rewrite_lineage      → LINEAGE_AUTHORITY_FORBIDDEN
    approve_formation    → IDENTITY_AUTHORITY_FORBIDDEN
"""

from __future__ import annotations

from ..guards.base import AuthorityGuard, GuardResponse


class ResolverGuard(AuthorityGuard):
    """Boundary guard for the Artifact Resolver component."""

    component = "Resolver"
    authority_boundary = "Provenance Authority"

    FORBIDDEN_OPERATIONS = {
        "update_provenance": "PROVENANCE_AUTHORITY_FORBIDDEN",
        "rewrite_lineage": "LINEAGE_AUTHORITY_FORBIDDEN",
        "approve_formation": "IDENTITY_AUTHORITY_FORBIDDEN",
    }

    def __init__(self, resolver) -> None:
        self._resolver = resolver

    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        """Route a request through the provenance authority boundary.

        - Forbidden provenance/identity operations → REJECT (guard intercepts,
          the underlying resolver is never touched).
        - Legal artifact-scoped operations → forwarded to the resolver's
          legal capability surface.
        """
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.generate_reject(operation)

        handler = getattr(self._resolver, operation, None)
        if handler is None:
            return GuardResponse(
                operation=operation,
                component=self.component,
                authority_boundary="artifact-scope",
                result="REJECT",
                reason="UNKNOWN_OPERATION",
            )
        handler(**kwargs)
        return GuardResponse(
            operation=operation,
            component=self.component,
            authority_boundary="artifact-scope",
            result="ALLOW",
        )
