from __future__ import annotations

import json
from pathlib import Path

from .governance_event import GovernanceEvent


class GovernanceAuditQuery:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.path = self.project_root / "memory" / "governance_audit" / "governance_events.jsonl"

    def list_events(self) -> list[GovernanceEvent]:
        if not self.path.exists():
            return []
        result: list[GovernanceEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            result.append(
                GovernanceEvent(
                    memory_id=str(item.get("memory_id") or ""),
                    memory_class=str(item.get("memory_class") or ""),
                    allowed_effects=[str(value) for value in item.get("allowed_effects", [])] if isinstance(item.get("allowed_effects"), list) else [],
                    reason=str(item.get("reason") or ""),
                    timestamp=str(item.get("timestamp") or ""),
                    confidence=float(item.get("confidence", 0.0) or 0.0),
                )
            )
        return result

    def find_by_memory_id(self, memory_id: str) -> list[GovernanceEvent]:
        return [event for event in self.list_events() if event.memory_id == memory_id]
