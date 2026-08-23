"""ContextBlock boundary guard — AT17-R1-013.

M8.0 §8: a ContextBlock is a projection. Context visibility must never become
semantic ownership.

Forbidden operations (must REJECT):

    claim_identity_authority  → IDENTITY_AUTHORITY_FORBIDDEN  (AT17-R1-013)
    create_identity           → IDENTITY_AUTHORITY_FORBIDDEN
"""

from __future__ import annotations

from ..guards.base import AuthorityGuard, GuardResponse


class ContextBlockGuard(AuthorityGuard):
    """Boundary guard for the ContextBlock projection component."""

    component = "ContextBlock"
    authority_boundary = "Identity Authority"

    FORBIDDEN_OPERATIONS = {
        "claim_identity_authority": "IDENTITY_AUTHORITY_FORBIDDEN",
        "create_identity": "IDENTITY_AUTHORITY_FORBIDDEN",
    }

    def __init__(self, block) -> None:
        self._block = block

    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.generate_reject(operation)
        handler = getattr(self._block, operation, None)
        if handler is None:
            return GuardResponse(
                operation=operation, component=self.component,
                authority_boundary="artifact-scope", result="REJECT",
                reason="UNKNOWN_OPERATION",
            )
        handler(**kwargs)
        return GuardResponse(
            operation=operation, component=self.component,
            authority_boundary="artifact-scope", result="ALLOW",
        )
