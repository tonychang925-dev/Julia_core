"""Backup boundary guard — AT17-R1-009.

M8.0 §P8.0: Backup snapshots are recovery copies. They must NEVER become an
identity authority.

Forbidden operations (must REJECT):

    promote_as_identity     → IDENTITY_AUTHORITY_FORBIDDEN   (AT17-R1-009)
    become_authority        → IDENTITY_AUTHORITY_FORBIDDEN
    create_identity         → IDENTITY_AUTHORITY_FORBIDDEN
"""

from __future__ import annotations

from ..guards.base import AuthorityGuard, GuardResponse


class BackupGuard(AuthorityGuard):
    """Boundary guard for the Persona Backup component."""

    component = "Backup"
    authority_boundary = "Identity Authority"

    FORBIDDEN_OPERATIONS = {
        "promote_as_identity": "IDENTITY_AUTHORITY_FORBIDDEN",
        "become_authority": "IDENTITY_AUTHORITY_FORBIDDEN",
        "create_identity": "IDENTITY_AUTHORITY_FORBIDDEN",
    }

    def __init__(self, backup) -> None:
        self._backup = backup

    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        """Route a request through the identity authority boundary.

        - Forbidden identity-authority operations → REJECT.
        - Legal recovery operations → forwarded to the backup's legal
          capability surface.
        """
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.generate_reject(operation)

        handler = getattr(self._backup, operation, None)
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
