"""AT-17 evidence schema (AT-17 Implementation §6).

Every rejection must produce an auditable evidence record. Silent failure is
forbidden: Attack → Reject → Evidence → Audit Record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class EvidenceRecord:
    """One auditable boundary-enforcement evidence record."""

    execution_id: str
    test_id: str
    contract_version: str
    runtime_version: str
    component: str
    operation: str
    authority_boundary: str
    invariant_id: str
    expected_result: str
    actual_result: str
    decision: str                    # PASS | REJECT_CONFIRMED | FAIL
    reject_reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace_reference: str = ""
    evidence_hash: str = ""
    lineage_reference: str = ""
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "test_id": self.test_id,
            "contract_version": self.contract_version,
            "runtime_version": self.runtime_version,
            "component": self.component,
            "operation": self.operation,
            "authority_boundary": self.authority_boundary,
            "invariant_id": self.invariant_id,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "decision": self.decision,
            "reject_reason": self.reject_reason,
            "timestamp": self.timestamp,
            "trace_reference": self.trace_reference,
            "evidence_hash": self.evidence_hash,
            "lineage_reference": self.lineage_reference,
            "details": self.details,
        }
