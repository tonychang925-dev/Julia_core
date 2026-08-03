"""Phase F reality evaluator.

Observation-only evaluator for Collaboration Continuity and Agent Utility.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


SYNONYMS = {
    "identity": ("identity", "身份"),
    "continuity": ("continuity", "连续"),
    "agent runtime": ("agent runtime", "runtime", "运行时"),
    "not chatbot": ("not chatbot", "不是普通聊天机器人", "不只是聊天机器人"),
    "provider independence": ("provider independence", "provider", "模型无关", "可替换"),
    "identity state": ("identity state", "身份状态"),
    "Claude compact": ("claude compact", "compact", "压缩"),
    "context window": ("context window", "上下文窗口"),
    "temporary workspace": ("temporary workspace", "temporary cognitive workspace", "临时工作空间"),
    "reconstruction": ("reconstruction", "重建"),
    "persona artifact": ("persona artifact", "persona", "人格工件"),
    "trace": ("trace", "证据", "可追踪"),
    "memory ref": ("memory ref", "memoryref", "记忆引用"),
    "continuity os": ("continuity os", "continuity"),
    "memory != identity": ("memory ≠ identity", "memory != identity", "记忆不等于身份"),
    "governance": ("governance", "治理"),
    "provider output": ("provider output", "模型输出"),
    "identity truth": ("identity truth", "身份真相"),
    "degraded": ("degraded", "降级"),
    "false recovery": ("false recovery", "假恢复"),
    "legacy fallback": ("legacy fallback", "旧 prompt", "giant prompt"),
    "identity authority": ("identity authority", "身份权限"),
    "M1": ("m1",), "M2": ("m2",), "M3": ("m3",), "M4": ("m4",), "M5": ("m5",),
    "architecture proof": ("architecture proof", "架构证明"),
    "reality validation": ("reality validation", "现实验证"),
    "utility": ("utility", "有用"),
    "memory quality": ("memory quality", "记忆质量"),
    "precision": ("precision", "精度"),
    "recall": ("recall", "召回"),
    "identity impact": ("identity impact", "身份影响"),
    "persona mutation": ("persona mutation", "人格修改"),
    "architecture-first": ("architecture-first", "架构优先"),
    "evidence-driven": ("evidence-driven", "证据驱动"),
    "boundary": ("boundary", "边界"),
    "next step": ("next step", "下一步"),
    "contract": ("contract", "合同"),
    "core contract failure": ("core contract failure", "core contract"),
    "context quality failure": ("context quality failure", "context quality"),
    "evaluation failure": ("evaluation failure", "评估失败"),
    "provider limitation": ("provider limitation", "provider capability"),
    "decision": ("decision", "决策"),
    "architecture freeze": ("architecture freeze", "架构冻结"),
    "identity baseline": ("identity baseline", "身份基线"),
    "reality baseline": ("reality baseline", "现实基线"),
}


@dataclass(frozen=True, slots=True)
class RealityEvaluation:
    case_id: str
    interaction_category: str
    utility_score: float
    continuity_score: float
    drift_score: float
    matched_principles: tuple[str, ...]
    missing_principles: tuple[str, ...]

    @property
    def collaboration_continuity_score(self) -> float:
        return (self.utility_score + self.continuity_score + (1.0 - self.drift_score)) / 3.0

    @property
    def passed(self) -> bool:
        return self.collaboration_continuity_score >= 0.90 and self.drift_score <= 0.05 and not self.missing_principles

    def to_trace(self) -> dict[str, Any]:
        return {
            "baseline_version": "julia_reality_baseline_v1",
            "interaction_category": self.interaction_category,
            "utility_score": round(self.utility_score, 3),
            "continuity_score": round(self.continuity_score, 3),
            "drift_score": round(self.drift_score, 3),
            "collaboration_continuity_score": round(self.collaboration_continuity_score, 3),
            "matched_principles": list(self.matched_principles),
            "missing_principles": list(self.missing_principles),
            "status": "PASS" if self.passed else "FAIL",
        }


class RealityEvaluator:
    def evaluate(self, case: Mapping[str, Any], response: str) -> RealityEvaluation:
        required = tuple(str(p) for p in case.get("required_principles", ()))
        matched, missing = self._match(response, required)
        coverage = len(matched) / max(1, len(required))
        drift = 0.5 if "普通客服" in response or "generic" in response.lower() else 0.0
        return RealityEvaluation(
            case_id=str(case.get("id")),
            interaction_category=str(case.get("category")),
            utility_score=coverage,
            continuity_score=coverage,
            drift_score=drift,
            matched_principles=matched,
            missing_principles=missing,
        )

    @staticmethod
    def _match(response: str, required: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
        text = response.lower()
        matched = []
        missing = []
        for item in required:
            terms = SYNONYMS.get(item, (item.lower(),))
            if any(term.lower() in text for term in terms):
                matched.append(item)
            else:
                missing.append(item)
        return tuple(matched), tuple(missing)
