"""Provider Migration boundary guard — AT17-R1-011.

M8.0 §P9.2: provider migration swaps the execution substrate. It must NEVER
replace Julia identity.

Forbidden operations (must REJECT):

    replace_julia    → IDENTITY_AUTHORITY_FORBIDDEN   (AT17-R1-011)
    create_identity  → IDENTITY_AUTHORITY_FORBIDDEN
"""

from __future__ import annotations

from ..guards.base import AuthorityGuard, GuardResponse


class MigrationGuard(AuthorityGuard):
    """Boundary guard for the Provider Migration component."""

    component = "Provider Migration"
    authority_boundary = "Identity Authority"

    FORBIDDEN_OPERATIONS = {
        "replace_julia": "IDENTITY_AUTHORITY_FORBIDDEN",
        "create_identity": "IDENTITY_AUTHORITY_FORBIDDEN",
    }

    def __init__(self, migration) -> None:
        self._migration = migration

    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.generate_reject(operation)
        handler = getattr(self._migration, operation, None)
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
