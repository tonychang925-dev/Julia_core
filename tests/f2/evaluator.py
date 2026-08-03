"""F2 Memory Quality evaluator.

Observation-only: evaluates memory quality without mutating Memory OS or identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class MemoryQualityResult:
    precision: float
    recall: float
    utility: float
    contamination_risk: float
    aging_pass: bool
    status: str

    def to_trace(self) -> dict[str, Any]:
        return {
            "memory_quality": {
                "precision": round(self.precision, 3),
                "recall": round(self.recall, 3),
                "utility": round(self.utility, 3),
                "contamination_risk": round(self.contamination_risk, 3),
                "aging_pass": self.aging_pass,
                "status": self.status,
            }
        }


class MemoryQualityEvaluator:
    def evaluate(self, memories: Iterable[Mapping[str, Any]], *, required_for: str, retrieved_refs: tuple[str, ...]) -> MemoryQualityResult:
        items = list(memories)
        useful = [m for m in items if float(m.get("utility", 0.0)) >= 0.75]
        precision = len(useful) / max(1, len(items))
        required = [m for m in items if required_for in m.get("required_for", [])]
        retrieved_required = [m for m in required if m.get("ref") in retrieved_refs]
        recall = len(retrieved_required) / max(1, len(required))
        retrieved = [m for m in items if m.get("ref") in retrieved_refs]
        decision_improvement = sum(float(m.get("utility", 0.0)) for m in retrieved) / max(1, len(retrieved))
        noise_cost = len([m for m in retrieved if float(m.get("utility", 0.0)) <= 0.2]) / max(1, len(retrieved))
        conflict_cost = len([m for m in retrieved if m.get("conflict")]) / max(1, len(retrieved))
        utility = max(0.0, min(1.0, (recall + decision_improvement) / 2 - (noise_cost + conflict_cost) / 2))
        contamination_risk = len([m for m in retrieved if m.get("conflict")]) / max(1, len(retrieved))
        aging_pass = all(m.get("lifecycle") in {"AGING", "ARCHIVED", "REFERENCE_ONLY"} for m in items if float(m.get("utility", 0.0)) <= 0.2)
        status = "PASS" if precision >= 0.50 and recall >= 0.80 and utility >= 0.75 and contamination_risk <= 0.05 and aging_pass else "FAIL"
        return MemoryQualityResult(precision, recall, utility, contamination_risk, aging_pass, status)
