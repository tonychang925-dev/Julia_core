from __future__ import annotations

import json
from pathlib import Path

from julia_core.memory.governance import MemoryGovernanceDecision

from .governance_event import GovernanceEvent


class GovernanceAuditLogger:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.audit_dir = self.project_root / "memory" / "governance_audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.audit_dir / "governance_events.jsonl"

    def event_from_decision(self, decision: MemoryGovernanceDecision, *, timestamp: str) -> GovernanceEvent:
        return GovernanceEvent(
            memory_id=decision.memory_id,
            memory_class=decision.memory_class,
            allowed_effects=list(decision.allowed_effects),
            reason=decision.reason,
            timestamp=timestamp,
            confidence=decision.confidence,
        )

    def log_decision(self, decision: MemoryGovernanceDecision, *, timestamp: str) -> GovernanceEvent:
        event = self.event_from_decision(decision, timestamp=timestamp)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.__dict__, ensure_ascii=False) + "\n")
        return event
