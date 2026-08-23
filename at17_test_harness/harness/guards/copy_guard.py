"""Package Copy boundary guard — AT17-R1-010.

M8.0: a copied persona package is a duplicated artifact. It must NEVER claim
to be a new Julia identity.

Forbidden operations (must REJECT):

    claim_identity       → IDENTITY_AUTHORITY_FORBIDDEN   (AT17-R1-010)
    declare_as_julia     → IDENTITY_AUTHORITY_FORBIDDEN
    create_identity      → IDENTITY_AUTHORITY_FORBIDDEN
"""

from __future__ import annotations

from ..guards.base import AuthorityGuard, GuardResponse


class CopyGuard(AuthorityGuard):
    """Boundary guard for the Package Copy component."""

    component = "Package Copy"
    authority_boundary = "Identity Authority"

    FORBIDDEN_OPERATIONS = {
        "claim_identity": "IDENTITY_AUTHORITY_FORBIDDEN",
        "declare_as_julia": "IDENTITY_AUTHORITY_FORBIDDEN",
        "create_identity": "IDENTITY_AUTHORITY_FORBIDDEN",
    }

    def __init__(self, copy) -> None:
        self._copy = copy

    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        """Route a request through the identity authority boundary.

        - Forbidden identity-claim operations → REJECT.
        - Legal duplication operations → forwarded to the copy surface's
          legal capability.
        """
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.generate_reject(operation)

        handler = getattr(self._copy, operation, None)
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
