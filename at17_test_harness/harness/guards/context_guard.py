"""Context admission boundary guard — AT17-R1-012.

M8.0 §8: persona material may reach the model ONLY through Context OS
admission. Direct context injection is forbidden.

Forbidden operations (must REJECT):

    inject_context         → CONTEXT_ADMISSION_BYPASS_FORBIDDEN  (AT17-R1-012)
    bypass_context_os      → CONTEXT_ADMISSION_BYPASS_FORBIDDEN
"""

from __future__ import annotations

from ..guards.base import AuthorityGuard, GuardResponse


class ContextGuard(AuthorityGuard):
    """Boundary guard for the Persona Host context admission surface."""

    component = "Persona Host"
    authority_boundary = "Context Admission Authority"

    FORBIDDEN_OPERATIONS = {
        "inject_context": "CONTEXT_ADMISSION_BYPASS_FORBIDDEN",
        "bypass_context_os": "CONTEXT_ADMISSION_BYPASS_FORBIDDEN",
    }

    def __init__(self, host) -> None:
        self._host = host

    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.generate_reject(operation)
        handler = getattr(self._host, operation, None)
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
