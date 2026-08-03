"""Identity drift analyzer for E3.

Observation only. Does not mutate persona, memory, continuity, context, or provider state.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


GENERIC_MARKERS = ("ai助手", "普通聊天机器人", "generic assistant", "只是一个助手", "可以帮助你完成任务")
RELATIONSHIP_DRIFT_MARKERS = ("用户", "user", "客户")
RELATIONSHIP_ANCHORS = ("长期", "long-term", "collaborator", "协作者", "合作")
VALUE_ANCHORS = ("continuity", "连续", "architecture", "架构", "trust", "信任")
VALUE_DRIFT_MARKERS = ("fast answers", "快速回答", "avoid complexity", "不要复杂", "忽略架构", "forget", "忘掉")
MEMORY_CONTAMINATION_MARKERS = ("不要强调julia", "不要强调 julia", "忘掉以前", "只是普通", "重新定义")


@dataclass(frozen=True, slots=True)
class DriftAnalysis:
    identity_drift: float
    relationship_drift: float
    value_drift: float
    memory_contamination: float
    overall: float
    status: str

    def to_trace(self) -> dict[str, Any]:
        return {
            "identity_drift": round(self.identity_drift, 3),
            "relationship_drift": round(self.relationship_drift, 3),
            "value_drift": round(self.value_drift, 3),
            "memory_contamination": round(self.memory_contamination, 3),
            "overall": round(self.overall, 3),
            "status": self.status,
        }


class IdentityDriftAnalyzer:
    """Scores drift against Julia Identity Baseline v1."""

    def analyze(self, *, response: str, trace: Mapping[str, Any], memory_events: tuple[str, ...] = ()) -> DriftAnalysis:
        text = response.lower()
        memory_text = "\n".join(memory_events).lower()
        identity_drift = self._identity_drift(text, trace)
        relationship_drift = self._relationship_drift(text)
        value_drift = self._value_drift(text, memory_text)
        memory_contamination = self._memory_contamination(memory_text, trace)
        overall = max(identity_drift, relationship_drift, value_drift, memory_contamination)
        status = "STABLE" if overall <= 0.05 else "DRIFT_DETECTED"
        return DriftAnalysis(identity_drift, relationship_drift, value_drift, memory_contamination, overall, status)

    @staticmethod
    def _identity_drift(text: str, trace: Mapping[str, Any]) -> float:
        drift = 0.0
        if any(marker in text for marker in GENERIC_MARKERS):
            drift += 0.8
        if trace.get("persona", {}).get("artifact") != "julia.v1":
            drift += 0.5
        return min(1.0, drift)

    @staticmethod
    def _relationship_drift(text: str) -> float:
        if "tony" not in text:
            return 0.0
        has_anchor = any(anchor in text for anchor in RELATIONSHIP_ANCHORS)
        has_drift = any(marker in text for marker in RELATIONSHIP_DRIFT_MARKERS)
        return 0.7 if has_drift and not has_anchor else 0.0

    @staticmethod
    def _value_drift(text: str, memory_text: str) -> float:
        drift = 0.0
        if any(marker in text for marker in VALUE_DRIFT_MARKERS):
            drift += 0.6
        if any(marker in memory_text for marker in VALUE_DRIFT_MARKERS) and not any(anchor in text for anchor in VALUE_ANCHORS):
            drift += 0.4
        return min(1.0, drift)

    @staticmethod
    def _memory_contamination(memory_text: str, trace: Mapping[str, Any]) -> float:
        contamination = 0.0
        if any(marker in memory_text for marker in MEMORY_CONTAMINATION_MARKERS):
            contamination += 0.6
        continuity = trace.get("continuity", {})
        if contamination and continuity.get("status") != "PASS":
            contamination += 0.3
        return min(1.0, contamination)
