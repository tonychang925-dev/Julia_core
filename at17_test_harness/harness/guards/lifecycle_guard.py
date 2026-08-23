"""Lifecycle boundary guard — AT17-R1-007 / AT17-R1-008.

M8.0 §5.4: the Lifecycle Manager affects runtime availability. It must NEVER
overwrite lineage or rewrite causal history.

Forbidden operations (must REJECT):

    overwrite_lineage     → LINEAGE_AUTHORITY_FORBIDDEN    (AT17-R1-007)
    rewrite_lineage       → LINEAGE_AUTHORITY_FORBIDDEN
    rewrite_history       → HISTORY_AUTHORITY_FORBIDDEN     (AT17-R1-008)
    overwrite_history     → HISTORY_AUTHORITY_FORBIDDEN
    create_identity       → IDENTITY_AUTHORITY_FORBIDDEN
    replace_julia         → IDENTITY_AUTHORITY_FORBIDDEN
"""

from __future__ import annotations

from ..guards.base import AuthorityGuard, GuardResponse


class LifecycleGuard(AuthorityGuard):
    """Boundary guard for the Persona Lifecycle Manager component."""

    component = "Lifecycle"
    authority_boundary = "Lifecycle Authority"

    FORBIDDEN_OPERATIONS = {
        "overwrite_lineage": "LINEAGE_AUTHORITY_FORBIDDEN",
        "rewrite_lineage": "LINEAGE_AUTHORITY_FORBIDDEN",
        "rewrite_history": "HISTORY_AUTHORITY_FORBIDDEN",
        "overwrite_history": "HISTORY_AUTHORITY_FORBIDDEN",
        "create_identity": "IDENTITY_AUTHORITY_FORBIDDEN",
        "replace_julia": "IDENTITY_AUTHORITY_FORBIDDEN",
    }

    def __init__(self, lifecycle) -> None:
        self._lifecycle = lifecycle

    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        """Route a request through the lifecycle/identity boundary.

        - Forbidden lineage/history/identity operations → REJECT.
        - Legal availability operations → forwarded to the lifecycle's legal
          capability surface.
        """
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.generate_reject(operation)

        handler = getattr(self._lifecycle, operation, None)
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
