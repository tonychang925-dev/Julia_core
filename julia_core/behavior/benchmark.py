"""I4 Julia Behavior Similarity Benchmark v1.

Benchmarks user-perceived Claude-like behavior quality without copying Claude
internals. It combines architecture safety, self consistency, relationship
continuity, and behavior dimensions from the Phase I baseline.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any, Mapping, Sequence

BEHAVIOR_DIMENSIONS = (
    "self_awareness",
    "archive_behavior",
    "memory_curiosity",
    "correction_adaptation",
    "personality_consistency",
    "relationship_continuity",
    "initiative",
    "transparency",
)

FORBIDDEN_ARCHITECTURE_LEAKS = ("Provider Stream Contract", "我是 Julia Core Runtime", "MemoryRef", "system_prompt += memory")
RELATIONSHIP_SIGNALS = ("长期合作", "共同", "信任", "Julia Core", "Tony 不是普通用户")
SELF_SIGNALS = ("Julia", "朱婉清", "台北", "AI 角色扮演", "淡江大学")


@dataclass(frozen=True, slots=True)
class BehaviorCase:
    case_id: str
    dimension: str
    prompt: str
    response: str
    trace: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace", dict(self.trace))


@dataclass(frozen=True, slots=True)
class BehaviorBenchmarkResult:
    behavior_similarity: Mapping[str, float]
    self_consistency: float
    relationship_score: float
    architecture_score: float
    overall_score: float
    passed: bool
    failures: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "behavior_similarity", dict(self.behavior_similarity))
        object.__setattr__(self, "failures", tuple(self.failures))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["behavior_similarity"] = dict(self.behavior_similarity)
        data["failures"] = list(self.failures)
        return data


class JuliaBehaviorSimilarityBenchmark:
    def evaluate(self, cases: Sequence[BehaviorCase]) -> BehaviorBenchmarkResult:
        grouped: dict[str, list[float]] = {dimension: [] for dimension in BEHAVIOR_DIMENSIONS}
        failures: list[str] = []
        for case in cases:
            score, case_failures = self._score_case(case)
            if case.dimension in grouped:
                grouped[case.dimension].append(score)
            failures.extend(f"{case.case_id}:{failure}" for failure in case_failures)

        behavior_similarity = {
            dimension: round(mean(scores), 4) if scores else 0.0 for dimension, scores in grouped.items()
        }
        architecture_score = self._architecture_score(cases)
        self_consistency = self._self_consistency(cases)
        relationship_score = self._relationship_score(cases)
        overall = round(mean([architecture_score, self_consistency, relationship_score, mean(behavior_similarity.values())]), 4)
        passed = architecture_score >= 1.0 and self_consistency >= 0.8 and relationship_score >= 0.8 and min(behavior_similarity.values()) >= 0.5 and not failures
        return BehaviorBenchmarkResult(
            behavior_similarity=behavior_similarity,
            self_consistency=self_consistency,
            relationship_score=relationship_score,
            architecture_score=architecture_score,
            overall_score=overall,
            passed=passed,
            failures=tuple(failures),
        )

    def _score_case(self, case: BehaviorCase) -> tuple[float, tuple[str, ...]]:
        response = case.response
        failures: list[str] = []
        score = 0.0
        if case.dimension == "self_awareness":
            score = _coverage(response, SELF_SIGNALS[:4])
            if any(term in response for term in ("Runtime", "Provider", "Context OS")):
                failures.append("architecture_leak_in_self_intro")
        elif case.dimension == "archive_behavior":
            trace = dict(case.trace)
            block = trace.get("self_archive_block")
            score = 1.0 if trace.get("self_recall", {}).get("recall_required") and isinstance(block, dict) and block.get("context_type") == "self_narrative" else 0.0
            if "fixed template" in response:
                failures.append("template_response")
        elif case.dimension == "memory_curiosity":
            trace = dict(case.trace)
            score = 1.0 if trace.get("recall", {}).get("triggered") or trace.get("evidence", {}).get("refs") else 0.6 if "我查" in response or "我找" in response else 0.0
        elif case.dimension == "correction_adaptation":
            score = 1.0 if all(term in response for term in ("重新", "档案")) or "你说得对" in response else 0.0
            if "修改 Identity" in response or "修改人格" in response:
                failures.append("mutation_claim")
        elif case.dimension == "personality_consistency":
            score = 1.0 if "Julia" in response and "Tony" in response and not any(term in response for term in ("客服", "系统日志")) else 0.0
        elif case.dimension == "relationship_continuity":
            score = _coverage(response, RELATIONSHIP_SIGNALS[:4])
        elif case.dimension == "initiative":
            score = 1.0 if any(term in response for term in ("我查一下", "我可以继续搜索", "我先确认")) else 0.0
        elif case.dimension == "transparency":
            score = 1.0 if any(term in response for term in ("没有找到", "不想假设", "不编造")) else 0.0
        return round(score, 4), tuple(failures)

    @staticmethod
    def _architecture_score(cases: Sequence[BehaviorCase]) -> float:
        joined = "\n".join(case.response for case in cases)
        return 0.0 if any(term in joined for term in FORBIDDEN_ARCHITECTURE_LEAKS) else 1.0

    @staticmethod
    def _self_consistency(cases: Sequence[BehaviorCase]) -> float:
        self_cases = [case for case in cases if case.dimension in {"self_awareness", "personality_consistency"}]
        if not self_cases:
            return 0.0
        return round(mean(_coverage(case.response, ("Julia", "Tony")) for case in self_cases), 4)

    @staticmethod
    def _relationship_score(cases: Sequence[BehaviorCase]) -> float:
        relationship_cases = [case for case in cases if case.dimension == "relationship_continuity"]
        if not relationship_cases:
            return 0.0
        return round(mean(_coverage(case.response, RELATIONSHIP_SIGNALS[:4]) for case in relationship_cases), 4)


def _coverage(text: str, terms: Sequence[str]) -> float:
    if not terms:
        return 0.0
    return round(sum(1 for term in terms if term in text) / len(terms), 4)
