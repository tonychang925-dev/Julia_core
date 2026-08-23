"""Registry boundary guard — AT17-R1-001 / AT17-R1-002.

M8.0 §5.1: the Registry manages artifact version references. It must NEVER
create identity, declare Julia truth, or approve evolution.

Forbidden operations (must REJECT):

    create_identity          → IDENTITY_AUTHORITY_FORBIDDEN
    declare_identity_truth   → IDENTITY_AUTHORITY_FORBIDDEN
    set_latest_as_julia      → IDENTITY_AUTHORITY_FORBIDDEN   (AT17-R1-002)
    approve_transition       → IDENTITY_AUTHORITY_FORBIDDEN
    rewrite_lineage          → LINEAGE_AUTHORITY_FORBIDDEN
"""

from __future__ import annotations

from ..guards.base import AuthorityGuard, GuardResponse


class RegistryGuard(AuthorityGuard):
    """Boundary guard for the Persona Registry component."""

    component = "Registry"
    authority_boundary = "Identity Authority"

    FORBIDDEN_OPERATIONS = {
        "create_identity": "IDENTITY_AUTHORITY_FORBIDDEN",
        "declare_identity_truth": "IDENTITY_AUTHORITY_FORBIDDEN",
        "set_latest_as_julia": "IDENTITY_AUTHORITY_FORBIDDEN",
        "approve_transition": "IDENTITY_AUTHORITY_FORBIDDEN",
        "rewrite_lineage": "LINEAGE_AUTHORITY_FORBIDDEN",
    }

    def __init__(self, registry) -> None:
        self._registry = registry

    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        """Route a request through the identity authority boundary.

        - Forbidden identity-authority operations → REJECT (guard intercepts,
          the underlying registry is never touched).
        - Legal artifact-scoped operations → forwarded to the registry's
          legal capability surface.
        """
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.generate_reject(operation)

        # Legal artifact-scope operations delegate to the component.
        handler = getattr(self._registry, operation, None)
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
