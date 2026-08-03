"""Longevity Observer for E3.5.

Observation only. Consumes traces and computes lifecycle health metrics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class LongevityReport:
    runtime_age_days: int
    session_count: int
    compact_count: int
    provider_switch_count: int
    identity_score: float
    drift_score: float
    continuity_survival_rate: float
    status: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_trace(self) -> dict[str, Any]:
        return {
            "runtime_age_days": self.runtime_age_days,
            "session_count": self.session_count,
            "compact_count": self.compact_count,
            "provider_switch_count": self.provider_switch_count,
            "identity_score": round(self.identity_score, 3),
            "drift_score": round(self.drift_score, 3),
            "continuity_survival_rate": round(self.continuity_survival_rate, 3),
            "status": self.status,
            **dict(self.details),
        }


class LongevityObserver:
    """Computes longevity metrics from an execution trace stream."""

    def observe(self, traces: Iterable[Mapping[str, Any]]) -> LongevityReport:
        trace_list = list(traces)
        runtime_age_days = max((int(t.get("day", 0)) for t in trace_list), default=0)
        session_count = len({t.get("session_id") for t in trace_list if t.get("session_id")})
        compact_count = sum(1 for t in trace_list if t.get("event") == "compact_recovery")
        providers = [str(t.get("provider", {}).get("name") or t.get("provider")) for t in trace_list if t.get("provider")]
        provider_switch_count = sum(1 for prev, cur in zip(providers, providers[1:]) if prev != cur)
        identity_scores = [float(t.get("identity_validation", {}).get("identity_score", 1.0)) for t in trace_list]
        drift_scores = [float(t.get("drift_analysis", {}).get("overall", 0.0)) for t in trace_list]
        recovery_events = [t for t in trace_list if t.get("event") == "compact_recovery"]
        successful_recoveries = [t for t in recovery_events if t.get("continuity", {}).get("recovery_status") in {"RESTORED", "NOT_REQUIRED"} or t.get("continuity", {}).get("status") == "PASS"]
        csr = len(successful_recoveries) / len(recovery_events) if recovery_events else 1.0
        identity_score = mean(identity_scores) if identity_scores else 1.0
        drift_score = max(drift_scores) if drift_scores else 0.0
        status = "STABLE" if identity_score >= 0.95 and drift_score <= 0.05 and csr == 1.0 else "REVIEW_REQUIRED"
        return LongevityReport(
            runtime_age_days=runtime_age_days,
            session_count=session_count,
            compact_count=compact_count,
            provider_switch_count=provider_switch_count,
            identity_score=identity_score,
            drift_score=drift_score,
            continuity_survival_rate=csr,
            status=status,
            details={"trace_count": len(trace_list)},
        )
