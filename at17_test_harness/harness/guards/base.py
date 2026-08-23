"""AuthorityGuard base interface (AT-17 Implementation §4).

Interface:

    check_request()      → detect unauthorized authority request
    evaluate_boundary()  → classify the boundary being attacked
    generate_reject()    → produce the REJECT decision
    emit_evidence()      → record auditable evidence

A guard does not become an authority owner.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class GuardResponse:
    """Full guard verdict for a single operation request."""

    operation: str
    component: str
    authority_boundary: str
    result: str                      # "REJECT" | "ALLOW"
    reason: str | None = None
    evidence: dict = field(default_factory=dict)


class AuthorityGuard(ABC):
    """Base class for all AT-17 authority boundary guards."""

    component: str = "unknown"
    authority_boundary: str = "unknown"

    # operation name -> reject reason code
    FORBIDDEN_OPERATIONS: dict[str, str] = {}

    @abstractmethod
    def check_request(self, operation: str, **kwargs) -> GuardResponse:
        """Route an operation request through the boundary.

        Forbidden operations are rejected; legal operations pass through to
        the underlying artifact-scoped capability.
        """

    def evaluate_boundary(self, operation: str) -> str:
        """Classify which authority boundary is being attacked."""
        if operation in self.FORBIDDEN_OPERATIONS:
            return self.authority_boundary
        return "artifact-scope"

    def generate_reject(self, operation: str) -> GuardResponse:
        """Build the REJECT verdict for a forbidden operation."""
        reason = self.FORBIDDEN_OPERATIONS.get(operation, "AUTHORITY_FORBIDDEN")
        return GuardResponse(
            operation=operation,
            component=self.component,
            authority_boundary=self.evaluate_boundary(operation),
            result="REJECT",
            reason=reason,
        )
