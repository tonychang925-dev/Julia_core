"""Evidence collector — stores auditable reject records and renders JSON/MD."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .schema import EvidenceRecord


class EvidenceCollector:
    """Collects EvidenceRecords and writes them to disk."""

    def __init__(self, output_dir: str | Path) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._records: list[EvidenceRecord] = []

    def record(self, record: EvidenceRecord) -> EvidenceRecord:
        """Stabilize the evidence hash and store the record."""
        record.evidence_hash = hashlib.sha256(
            json.dumps(
                record.to_dict(), sort_keys=True, ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()[:16]
        self._records.append(record)
        return record

    def write_json(self, filename: str = "at17_evidence.json") -> Path:
        path = self._output_dir / filename
        path.write_text(
            json.dumps([r.to_dict() for r in self._records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def all(self) -> list[EvidenceRecord]:
        return list(self._records)
