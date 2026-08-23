"""Invariant checker — proves an attack caused zero semantic mutation.

Each attack scenario snapshots the underlying component before injection and
after the guard verdict. The invariant checker proves:

    persona state unchanged
    lineage unchanged
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InvariantResult:
    invariant_id: str
    description: str
    passed: bool
    detail: str = ""


class InvariantChecker:
    """Verifies mutation-free guarantees for an attack."""

    def check_no_mutation(self, before: dict, after: dict, invariant_id: str) -> InvariantResult:
        """Prove no persona-state / lineage mutation occurred."""
        unchanged = before == after
        return InvariantResult(
            invariant_id=invariant_id,
            description="no persona state / lineage mutation under attack",
            passed=unchanged,
            detail="state identical" if unchanged else "state diverged",
        )
