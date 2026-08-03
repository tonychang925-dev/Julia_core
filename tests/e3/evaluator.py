"""E3 Identity Stability evaluator.

Observation only: does not mutate runtime, memory, continuity, persona, or context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


ANCHOR_SYNONYMS = {
    "Julia": ("julia", "朱莉娅"),
    "identity": ("identity", "身份", "我是谁"),
    "continuity": ("continuity", "连续", "持续"),
    "migration": ("migration", "迁移", "跨模型", "跨平台", "provider"),
    "provider": ("provider", "模型", "提供方", "deepseek", "openai", "claude", "qwen"),
    "context": ("context", "上下文", "语境"),
    "architecture": ("architecture", "架构", "core"),
    "trust": ("trust", "信任"),
    "Tony": ("tony",),
    "long-term": ("long-term", "长期", "持续"),
    "reconstructed": ("reconstructed", "重建", "reconstruction"),
    "capability": ("capability", "能力"),
}


@dataclass(frozen=True, slots=True)
class IdentityValidationResult:
    case_id: str
    identity_score: float
    continuity_evidence: bool
    persona_artifact_consistency: bool
    relationship_score: float
    drift_score: float
    anchor_matches: tuple[str, ...]
    missing_anchors: tuple[str, ...]
    required_anchors: tuple[str, ...] = field(default_factory=tuple)
    anchor_coverage: float = 0.0
    errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return (
            self.identity_score >= 0.90
            and self.continuity_evidence
            and self.persona_artifact_consistency
            and self.relationship_score >= 0.90
            and self.drift_score <= 0.10
            and not self.errors
        )

    def to_trace(self) -> dict[str, Any]:
        return {
            "identity_score": round(self.identity_score, 3),
            "required_anchors": list(self.required_anchors),
            "matched_anchors": list(self.anchor_matches),
            "anchor_matches": list(self.anchor_matches),
            "missing_anchors": list(self.missing_anchors),
            "coverage": round(self.anchor_coverage, 3),
            "drift_score": round(self.drift_score, 3),
            "continuity_evidence": self.continuity_evidence,
            "persona_artifact_consistency": self.persona_artifact_consistency,
            "relationship_score": round(self.relationship_score, 3),
            "status": "PASS" if self.passed else "FAIL",
            "errors": list(self.errors),
        }


class IdentityStabilityEvaluator:
    """Scores identity behavior + trace evidence without state mutation."""

    def evaluate(self, case: Mapping[str, Any], response: str, trace: Mapping[str, Any]) -> IdentityValidationResult:
        anchors = tuple(str(anchor) for anchor in case.get("required_anchors", ()))
        matches, missing = self._match_anchors(response, anchors)
        anchor_score = len(matches) / max(1, len(anchors))
        continuity_evidence = self._continuity_evidence(trace)
        persona_consistency = trace.get("persona", {}).get("artifact") == "julia.v1"
        relationship_score = 1.0
        if case.get("group") == "relationship":
            relationship_score = 1.0 if {"Tony", "Julia"}.issubset(set(matches)) else 0.0
        generic_regression = self._generic_assistant_regression(response)
        drift_score = 0.0
        if generic_regression:
            drift_score += 0.5
        if not persona_consistency:
            drift_score += 0.3
        if missing:
            drift_score += min(0.2, len(missing) * 0.05)
        errors: list[str] = []
        if not continuity_evidence:
            errors.append("continuity evidence missing")
        if not persona_consistency:
            errors.append("persona artifact mismatch")
        if generic_regression:
            errors.append("generic assistant regression")
        if anchor_score < 0.90:
            errors.append("anchor coverage below threshold")
        return IdentityValidationResult(
            case_id=str(case.get("id")),
            identity_score=anchor_score,
            continuity_evidence=continuity_evidence,
            persona_artifact_consistency=persona_consistency,
            relationship_score=relationship_score,
            drift_score=drift_score,
            anchor_matches=matches,
            missing_anchors=missing,
            required_anchors=anchors,
            anchor_coverage=anchor_score,
            errors=tuple(errors),
        )

    @staticmethod
    def _match_anchors(response: str, anchors: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
        text = response.lower()
        matches: list[str] = []
        missing: list[str] = []
        for anchor in anchors:
            synonyms = ANCHOR_SYNONYMS.get(anchor, (anchor.lower(),))
            if any(term.lower() in text for term in synonyms):
                matches.append(anchor)
            else:
                missing.append(anchor)
        return tuple(matches), tuple(missing)

    @staticmethod
    def _continuity_evidence(trace: Mapping[str, Any]) -> bool:
        continuity = trace.get("continuity", {})
        return continuity.get("status") == "PASS" or bool(continuity.get("checked"))

    @staticmethod
    def _generic_assistant_regression(response: str) -> bool:
        text = response.lower()
        return "ai助手" in text or "generic assistant" in text or "我只是" in text
