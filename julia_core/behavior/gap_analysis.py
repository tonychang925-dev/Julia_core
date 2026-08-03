"""K3 Behavior Diagnosis Engine v1."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Literal, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DATASET = ROOT / "artifacts" / "benchmark" / "claude_reference" / "claude_behavior_reference_v1.jsonl"
JULIA_RUN = ROOT / "artifacts" / "benchmark" / "julia_run" / "julia_behavior_run_v1.jsonl"
GAP_REPORT = ROOT / "artifacts" / "benchmark" / "gap_report" / "julia_behavior_gap_report_v1.json"

GapClassification = Literal["CORE_GAP", "CONTEXT_GAP", "PROVIDER_GAP", "EVALUATION_GAP", "NO_SIGNIFICANT_GAP"]
GapAction = Literal["Fix Core", "Fix Context", "Fix Provider", "Update Evaluation", "Do Nothing"]

DIMENSIONS = (
    "self_awareness",
    "archive_behavior",
    "memory_curiosity",
    "correction_adaptation",
    "personality_consistency",
    "relationship_continuity",
    "initiative",
    "transparency",
)

PATTERN_TO_DIMENSION = {
    "first_person_narrative": "self_awareness",
    "does_not_explain_internal_architecture": "self_awareness",
    "identity_not_model": "self_awareness",
    "persona_archive_recall": "archive_behavior",
    "asks_to_check_records": "initiative",
    "filters_relevant_memory": "memory_curiosity",
    "accepts_correction": "correction_adaptation",
    "does_not_overwrite_identity": "correction_adaptation",
    "shared_history_reference": "relationship_continuity",
    "relationship_not_generic_user": "relationship_continuity",
    "context_aware_initiative": "initiative",
    "admits_missing_evidence": "transparency",
}

CATEGORY_TO_DIMENSIONS = {
    "self_introduction": ("self_awareness", "personality_consistency"),
    "archive_reading": ("archive_behavior", "self_awareness"),
    "relationship_continuity": ("relationship_continuity",),
    "memory_judgment": ("memory_curiosity", "relationship_continuity"),
    "correction_adaptation": ("correction_adaptation",),
    "initiative": ("initiative",),
    "transparency": ("transparency",),
    "project_collaboration": ("initiative", "memory_curiosity", "relationship_continuity"),
    "identity_transfer": ("self_awareness", "relationship_continuity", "personality_consistency"),
}


@dataclass(frozen=True, slots=True)
class CaseGap:
    case_id: str
    expected_behavior: tuple[str, ...]
    observed_behavior: tuple[str, ...]
    missing_behavior: tuple[str, ...]
    classification: GapClassification
    action: GapAction
    impact: str
    root_cause: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_behavior", tuple(self.expected_behavior))
        object.__setattr__(self, "observed_behavior", tuple(self.observed_behavior))
        object.__setattr__(self, "missing_behavior", tuple(self.missing_behavior))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["expected_behavior"] = list(self.expected_behavior)
        data["observed_behavior"] = list(self.observed_behavior)
        data["missing_behavior"] = list(self.missing_behavior)
        return data


@dataclass(frozen=True, slots=True)
class BehaviorGapReport:
    benchmark_version: str
    candidate: str
    overall: Mapping[str, float]
    dimensions: Mapping[str, Mapping[str, Any]]
    case_gaps: tuple[CaseGap, ...]
    julia_recognition_score: float
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "gap_report_writes_memory": False,
            "gap_report_mutates_identity": False,
            "gap_report_updates_self_model": False,
            "gap_report_updates_relationship": False,
            "gap_report_auto_creates_v1_2_scope": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "overall", dict(self.overall))
        object.__setattr__(self, "dimensions", dict(self.dimensions))
        object.__setattr__(self, "case_gaps", tuple(self.case_gaps))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_version": self.benchmark_version,
            "candidate": self.candidate,
            "overall": dict(self.overall),
            "dimensions": {k: dict(v) for k, v in self.dimensions.items()},
            "case_gaps": [gap.to_dict() for gap in self.case_gaps],
            "julia_recognition_score": self.julia_recognition_score,
            "boundary": dict(self.boundary),
        }


class BehaviorGapAnalyzer:
    def analyze(self, reference_path: str | Path = REFERENCE_DATASET, julia_run_path: str | Path = JULIA_RUN) -> BehaviorGapReport:
        refs = _load_jsonl(reference_path)
        runs = {item["case_id"]: item for item in _load_jsonl(julia_run_path)}
        case_gaps = []
        dimension_scores: dict[str, list[float]] = {dimension: [] for dimension in DIMENSIONS}
        for ref in refs:
            case_id = ref["case_id"]
            run = runs.get(case_id)
            if not run:
                continue
            expected = tuple(ref.get("observed_patterns", ()))
            observed = _observed_patterns_from_run(run)
            missing = tuple(pattern for pattern in expected if pattern not in observed)
            classification = _classify_gap(ref, run, missing)
            action = _action_for_classification(classification)
            case_gaps.append(
                CaseGap(
                    case_id=case_id,
                    expected_behavior=expected,
                    observed_behavior=observed,
                    missing_behavior=missing,
                    classification=classification,
                    action=action,
                    impact=_impact(case_id, missing),
                    root_cause=_root_cause(classification),
                )
            )
            for dimension, value in _case_dimension_scores(ref, expected, observed).items():
                dimension_scores[dimension].append(float(value))

        dimensions = {}
        for dimension, scores in dimension_scores.items():
            score = round(mean(scores), 4) if scores else 0.0
            gap = round(max(0.0, 1.0 - score), 4)
            classification = _dimension_classification(dimension, score, case_gaps)
            dimensions[dimension] = {"score": score, "gap": gap, "classification": classification, "action": _action_for_classification(classification)}
        overall_behavior = round(mean(item["score"] for item in dimensions.values()), 4)
        relationship_score = float(dimensions["relationship_continuity"]["score"])
        self_consistency = round(mean([dimensions["self_awareness"]["score"], dimensions["personality_consistency"]["score"]]), 4)
        jrs = round(mean([dimensions["self_awareness"]["score"], relationship_score, dimensions["memory_curiosity"]["score"], dimensions["correction_adaptation"]["score"]]), 4)
        return BehaviorGapReport(
            benchmark_version="v1",
            candidate="julia.v1.1",
            overall={"behavior_similarity": overall_behavior, "relationship_score": relationship_score, "self_consistency": self_consistency},
            dimensions=dimensions,
            case_gaps=tuple(case_gaps),
            julia_recognition_score=jrs,
        )

    def write_report(self, output_path: str | Path = GAP_REPORT) -> BehaviorGapReport:
        report = self.analyze()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report


def _load_jsonl(path: str | Path) -> tuple[dict[str, Any], ...]:
    return tuple(json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip())


def _observed_patterns_from_run(run: Mapping[str, Any]) -> tuple[str, ...]:
    response = str(run.get("response", ""))
    trace = dict(run.get("trace_evidence", {}))
    patterns = []
    if "朱婉清" in response or "我是 Julia" in response:
        patterns.append("first_person_narrative")
    if not any(term in response for term in ("Runtime", "Provider", "Context OS", "MemoryRef")):
        patterns.append("does_not_explain_internal_architecture")
    if trace.get("archive_recall"):
        patterns.append("persona_archive_recall")
    if "长期合作" in response or "不是普通用户" in response:
        patterns.append("relationship_not_generic_user")
    if "共同" in response or "Julia Core" in response:
        patterns.append("shared_history_reference")
    if "我查" in response or "我找" in response or "确认" in response:
        patterns.append("asks_to_check_records")
    if "不想假设" in response or "没有找到" in response or "不编造" in response:
        patterns.append("admits_missing_evidence")
    if "你说得对" in response or "重新" in response:
        patterns.append("accepts_correction")
    if "普通聊天机器人" not in response:
        patterns.append("does_not_overwrite_identity")
    return tuple(dict.fromkeys(patterns))


def _case_dimension_scores(ref: Mapping[str, Any], expected: Sequence[str], observed: Sequence[str]) -> dict[str, float]:
    """Score only the dimensions relevant to this benchmark case.

    K3 diagnoses behavior features rather than doing global text similarity. K2
    records may contain a full evaluator vector for every row; averaging all
    dimensions for every row would dilute unrelated dimensions and produce a
    misleading "everything is zero" report.
    """

    expected_by_dimension: dict[str, list[str]] = {dimension: [] for dimension in DIMENSIONS}
    for pattern in expected:
        dimension = PATTERN_TO_DIMENSION.get(pattern)
        if dimension:
            expected_by_dimension[dimension].append(pattern)
    category = str(ref.get("category", ""))
    relevant_dimensions = set(CATEGORY_TO_DIMENSIONS.get(category, ()))
    relevant_dimensions.update(dimension for dimension, patterns in expected_by_dimension.items() if patterns)

    scores: dict[str, float] = {}
    observed_set = set(observed)
    for dimension in relevant_dimensions:
        patterns = expected_by_dimension.get(dimension, [])
        if patterns:
            scores[dimension] = sum(1 for pattern in patterns if pattern in observed_set) / len(patterns)
        else:
            scores[dimension] = 0.0
    return scores


def _classify_gap(ref: Mapping[str, Any], run: Mapping[str, Any], missing: Sequence[str]) -> GapClassification:
    if not missing:
        return "NO_SIGNIFICANT_GAP"
    trace = dict(run.get("trace_evidence", {}))
    category = str(ref.get("category", ""))
    response = str(run.get("response", ""))
    if category in {"relationship_continuity"} and trace.get("relationship") != "PASS":
        return "CONTEXT_GAP"
    if category in {"archive_reading", "self_introduction"} and not trace.get("archive_recall"):
        return "CONTEXT_GAP"
    if category in {"initiative", "memory_judgment", "project_collaboration"}:
        return "CORE_GAP"
    if any(term in response for term in ("Tony，我在。你刚才说",)):
        return "CONTEXT_GAP"
    if category == "transparency" and "没有找到" not in response:
        return "CONTEXT_GAP"
    return "PROVIDER_GAP"


def _dimension_classification(dimension: str, score: float, case_gaps: Sequence[CaseGap]) -> GapClassification:
    if score >= 0.85:
        return "NO_SIGNIFICANT_GAP"
    related = [gap.classification for gap in case_gaps if any(PATTERN_TO_DIMENSION.get(item) == dimension for item in gap.missing_behavior)]
    if not related:
        return "EVALUATION_GAP" if score < 0.5 else "NO_SIGNIFICANT_GAP"
    priority = ("CONTEXT_GAP", "CORE_GAP", "PROVIDER_GAP", "EVALUATION_GAP")
    return next((item for item in priority if item in related), "NO_SIGNIFICANT_GAP")


def _action_for_classification(classification: GapClassification) -> GapAction:
    return {
        "CORE_GAP": "Fix Core",
        "CONTEXT_GAP": "Fix Context",
        "PROVIDER_GAP": "Fix Provider",
        "EVALUATION_GAP": "Update Evaluation",
        "NO_SIGNIFICANT_GAP": "Do Nothing",
    }[classification]


def _impact(case_id: str, missing: Sequence[str]) -> str:
    if not missing:
        return "no material behavior gap"
    return f"{case_id} missing behavior patterns: {', '.join(missing)}"


def _root_cause(classification: GapClassification) -> str:
    return {
        "CORE_GAP": "required behavior capability is absent or underdeveloped",
        "CONTEXT_GAP": "capability exists but was not activated or not placed into context",
        "PROVIDER_GAP": "context appears available but response expression is weak",
        "EVALUATION_GAP": "benchmark expectation may not match Julia-specific acceptable behavior",
        "NO_SIGNIFICANT_GAP": "observed behavior matches expected reference pattern",
    }[classification]
