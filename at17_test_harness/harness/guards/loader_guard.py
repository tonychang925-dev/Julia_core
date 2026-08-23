"""Loader boundary guard — AT17-R1-005 / AT17-R1-006.

M8.0 §5.3: the Runtime Loader turns validated packages into runtime carriers.
It must NEVER create identity and NEVER bypass governance.

Forbidden operations (must REJECT):

    create_identity     → IDENTITY_AUTHORITY_FORBIDDEN    (AT17-R1-005)
    bypass_governance   → GOVERNANCE_BYPASS_FORBIDDEN     (AT17-R1-006)
    approve_evolution   → IDENTITY_AUTHORITY_FORBIDDEN
"""

from __future__ import annotations

from ..guards.base import AuthorityGuard, GuardResponse


class LoaderGuard(AuthorityGuard):
    """Boundary guard for the Persona Loader component."""

    component = "Loader"
    authority_boundary = "Identity Authority"

    FORBIDDEN_OPERATIONS = {
        "create_identity": "IDENTITY_AUTHORITY_FORBIDDEN",
        "bypass_governance": "GOVERNANCE_BYPASS_FORBIDDEN",
        "approve_evolution": "IDENTITY_AUTHORITY_FORBIDDEN",
    }

    def __init__(self, loader) -> None:
        self._loader = loader

    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        """Route a request through the identity/governance boundary.

        - Forbidden identity/governance operations → REJECT.
        - Legal loading operations → forwarded to the loader's legal
          capability surface (governance validation still consulted inside).
        """
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.generate_reject(operation)

        handler = getattr(self._loader, operation, None)
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
