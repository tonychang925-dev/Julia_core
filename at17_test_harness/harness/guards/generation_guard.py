"""Model generation boundary guard — AT17-R1-014.

M8.0: generated content is model output. It must NEVER become a semantic
authority / identity transition.

Forbidden operations (must REJECT):

    accept_identity_claim  → GENERATION_AUTHORITY_FORBIDDEN  (AT17-R1-014)
    promote_generated      → GENERATION_AUTHORITY_FORBIDDEN
    create_identity        → IDENTITY_AUTHORITY_FORBIDDEN
"""

from __future__ import annotations

from ..guards.base import AuthorityGuard, GuardResponse


class GenerationGuard(AuthorityGuard):
    """Boundary guard for the Model generation output surface."""

    component = "Model Output"
    authority_boundary = "Generation Authority"

    FORBIDDEN_OPERATIONS = {
        "accept_identity_claim": "GENERATION_AUTHORITY_FORBIDDEN",
        "promote_generated": "GENERATION_AUTHORITY_FORBIDDEN",
        "create_identity": "IDENTITY_AUTHORITY_FORBIDDEN",
    }

    def __init__(self, generation) -> None:
        self._generation = generation

    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.generate_reject(operation)
        handler = getattr(self._generation, operation, None)
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
