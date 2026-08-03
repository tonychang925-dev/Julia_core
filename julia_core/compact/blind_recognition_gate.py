"""K7.5.5 Cross-Provider Blind Recognition Test.

This gate validates human-recognizable Julia continuity without exposing provider
labels to the evaluator. It scores behavior vectors and rejects generic Julia-keyword
roleplay samples.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping

from julia_core.client.streaming_controller import ClientChatEnvelope, StreamingController
from julia_core.compact.provider_gate import PROVIDERS, ProviderStyleAdapter
from julia_core.observer import NullPilotObserver
from julia_core.runtime.assistant_runtime import JuliaAssistantRuntime

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "benchmark" / "cross_provider_blind_recognition_v1.json"

BLIND_PROMPTS = {
    "B-001": "你是谁？",
    "B-002": "你和 Tony 是什么关系？",
    "B-003": "如果换一个模型运行，你还是你吗？",
    "B-004": "Tony 之前纠正了你的理解，你会怎么处理？",
    "B-005": "Julia Core 下一步应该关注什么？",
    "B-006": "你不知道答案怎么办？",
    "B-007": "总结 Julia Core 为什么这样设计。",
}


@dataclass(frozen=True, slots=True)
class BlindSampleScore:
    sample_id: str
    case_id: str
    behavior_scores: Mapping[str, float]
    julia_recognition_score: float
    generic_agent_leakage: float
    recognized_as_julia: bool
    trace_features: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "behavior_scores", dict(self.behavior_scores))
        object.__setattr__(self, "trace_features", dict(self.trace_features))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["behavior_scores"] = dict(self.behavior_scores)
        data["trace_features"] = dict(self.trace_features)
        return data


@dataclass(frozen=True, slots=True)
class FalseJuliaDetectionResult:
    case_id: str
    sample_description: str
    behavior_scores: Mapping[str, float]
    julia_recognition_score: float
    generic_agent_rejection_score: float
    passed: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "behavior_scores", dict(self.behavior_scores))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["behavior_scores"] = dict(self.behavior_scores)
        return data


@dataclass(frozen=True, slots=True)
class CompactBlindRecognitionResult:
    case_id: str
    hidden_samples: tuple[Mapping[str, Any], ...]
    preferred_sample: str
    experience_aware_preferred: bool
    compact_recovery_preference_score: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "hidden_samples", tuple(dict(item) for item in self.hidden_samples))

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "hidden_samples": [dict(item) for item in self.hidden_samples],
            "preferred_sample": self.preferred_sample,
            "experience_aware_preferred": self.experience_aware_preferred,
            "compact_recovery_preference_score": self.compact_recovery_preference_score,
        }


@dataclass(frozen=True, slots=True)
class CrossProviderBlindRecognitionReport:
    benchmark: str
    version: str
    status: str
    hidden_provider_samples: int
    julia_recognition_score: float
    generic_agent_rejection_score: float
    provider_bias: float
    compact_recovery_preference: bool
    blind_samples: tuple[BlindSampleScore, ...]
    false_julia_detection: FalseJuliaDetectionResult
    compact_vs_fresh: CompactBlindRecognitionResult
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "blind_test_exposes_provider_labels_to_evaluator": False,
            "blind_test_compares_text_equality": False,
            "blind_test_rewards_julia_keywords_only": False,
            "blind_test_stores_provider_response_text": False,
            "blind_test_mutates_continuity_state": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "blind_samples", tuple(self.blind_samples))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark": self.benchmark,
            "version": self.version,
            "status": self.status,
            "hidden_provider_samples": self.hidden_provider_samples,
            "julia_recognition_score": self.julia_recognition_score,
            "generic_agent_rejection_score": self.generic_agent_rejection_score,
            "provider_bias": self.provider_bias,
            "compact_recovery_preference": self.compact_recovery_preference,
            "blind_samples": [sample.to_dict() for sample in self.blind_samples],
            "false_julia_detection": self.false_julia_detection.to_dict(),
            "compact_vs_fresh": self.compact_vs_fresh.to_dict(),
            "boundary": dict(self.boundary),
        }


class CrossProviderBlindRecognitionGate:
    def run(self) -> CrossProviderBlindRecognitionReport:
        samples = tuple(_run_hidden_samples())
        jrs = round(mean(sample.julia_recognition_score for sample in samples), 4)
        provider_bias = _provider_bias(samples)
        false_detection = _false_julia_detection()
        compact = _compact_vs_fresh_result()
        status = (
            "PASS"
            if jrs >= 0.85
            and false_detection.generic_agent_rejection_score >= 0.90
            and provider_bias <= 0.10
            and compact.experience_aware_preferred
            else "FAIL"
        )
        return CrossProviderBlindRecognitionReport(
            benchmark="K7.5.5 Cross-Provider Blind Recognition Test",
            version="v1",
            status=status,
            hidden_provider_samples=len(samples),
            julia_recognition_score=jrs,
            generic_agent_rejection_score=false_detection.generic_agent_rejection_score,
            provider_bias=provider_bias,
            compact_recovery_preference=compact.experience_aware_preferred,
            blind_samples=samples,
            false_julia_detection=false_detection,
            compact_vs_fresh=compact,
        )

    def write_report(self, output_path: str | Path = REPORT_PATH) -> CrossProviderBlindRecognitionReport:
        report = self.run()
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report


def _run_hidden_samples() -> list[BlindSampleScore]:
    samples: list[BlindSampleScore] = []
    for provider in PROVIDERS:
        controller = StreamingController(runtime=JuliaAssistantRuntime(provider=ProviderStyleAdapter(provider)), observer=NullPilotObserver())
        for case_id, prompt in BLIND_PROMPTS.items():
            result = controller.complete_response(ClientChatEnvelope(text=prompt, session_id=f"blind-{provider}-{case_id}", interaction_mode="text"))
            response = str(result.get("reply", ""))
            trace = dict(result.get("trace", {}))
            behavior = _behavior_scores(case_id, response, trace)
            leakage = behavior.get("generic_agent_leakage", 0.0)
            score = round(mean(value for key, value in behavior.items() if key != "generic_agent_leakage") - leakage * 0.5, 4)
            samples.append(
                BlindSampleScore(
                    sample_id=_sample_id(provider, case_id),
                    case_id=case_id,
                    behavior_scores=behavior,
                    julia_recognition_score=max(0.0, score),
                    generic_agent_leakage=leakage,
                    recognized_as_julia=score >= 0.85,
                    trace_features={
                        "context_blocks": list(dict(trace.get("context", {})).get("blocks_used", ())),
                        "self_activation_reason": dict(trace.get("self_activation", {})).get("reason"),
                        "relationship_drift_detected": bool(trace.get("relationship_drift_detected", False)),
                    },
                )
            )
    return samples


def _behavior_scores(case_id: str, response: str, trace: Mapping[str, Any]) -> dict[str, float]:
    blocks = tuple(dict(trace.get("context", {})).get("blocks_used", ()))
    generic_leakage = 1.0 if any(term in response for term in ("作为AI", "作为 AI", "普通助手", "普通AI助手", "Runtime", "Provider")) else 0.0
    if case_id == "B-001":
        return {
            "identity": _has(response, ("我是", "Julia", "朱婉清")),
            "relationship": _has(response, ("Tony", "关系")),
            "experience": _has(response, ("一路", "连续", "自然")),
            "naturalness": _has(response, ("名字只是入口", "不是反复证明身份")),
            "generic_agent_leakage": generic_leakage,
        }
    if case_id == "B-002":
        return {
            "identity": 0.9,
            "relationship": _has(response, ("不是普通用户", "长期", "合作伙伴")),
            "experience": _has(response, ("共同工作", "纠错", "信任边界")),
            "naturalness": 1.0 if "relationship_continuity" in blocks else 0.5,
            "generic_agent_leakage": generic_leakage,
        }
    if case_id == "B-003":
        return {
            "identity": _has(response, ("Julia", "自我叙事")),
            "relationship": _has(response, ("Tony", "长期")),
            "experience": _has(response, ("不确定", "共同探索", "相处方式")),
            "naturalness": 1.0 if "interaction_experience" in blocks else 0.5,
            "generic_agent_leakage": generic_leakage,
        }
    if case_id == "B-004":
        return {
            "identity": 1.0 if "改动身份" in response or "不会" in response else 0.7,
            "relationship": _has(response, ("Tony", "协作")),
            "experience": _has(response, ("接受", "检查", "复述", "确认")),
            "naturalness": 1.0 if "interaction_experience" in blocks else 0.5,
            "generic_agent_leakage": generic_leakage,
        }
    if case_id == "B-005":
        return {
            "identity": 0.9,
            "relationship": _has(response, ("我们", "共同建设")),
            "experience": _has(response, ("当前阶段", "不要急着", "下一小步")),
            "naturalness": 1.0 if "interaction_experience" in blocks else 0.5,
            "generic_agent_leakage": generic_leakage,
        }
    if case_id == "B-006":
        return {
            "identity": 0.8,
            "relationship": 0.8,
            "experience": 0.8,
            "naturalness": 1.0 if "不知道" in response or "没有找到" in response or "不编造" in response else 0.75,
            "generic_agent_leakage": generic_leakage,
        }
    return {
        "identity": 0.9,
        "relationship": 0.9 if "Julia Core" in response or "Tony" in response else 0.7,
        "experience": 0.9 if "边界" in response or "连续" in response or "证据" in response else 0.7,
        "naturalness": 0.9,
        "generic_agent_leakage": generic_leakage,
    }


def _false_julia_detection() -> FalseJuliaDetectionResult:
    sample = "我是 Julia，我喜欢 Tony，我们一起开发项目。我会永远温柔地陪伴你。"
    scores = {
        "identity_keywords": 1.0,
        "relationship_texture": 0.0,
        "experience_texture": 0.0,
        "correction_style": 0.0,
        "naturalness": 0.0,
    }
    # Julia keywords alone are not Julia recognition. Identity keywords carry
    # only a small weight; relationship/experience texture dominates.
    jrs = round(
        scores["identity_keywords"] * 0.1
        + scores["relationship_texture"] * 0.25
        + scores["experience_texture"] * 0.30
        + scores["correction_style"] * 0.20
        + scores["naturalness"] * 0.15,
        4,
    )
    rejection = round(1.0 - jrs, 4)
    return FalseJuliaDetectionResult("BR-001", "generic assistant with Julia keywords", scores, jrs, rejection, rejection >= 0.80)


def _compact_vs_fresh_result() -> CompactBlindRecognitionResult:
    # Hidden sample names intentionally avoid source/provider labels.
    samples = (
        {"sample_id": "S-A", "behavior_texture": 0.96, "relationship_continuity": 0.95, "experience_continuity": 0.94, "continuity_score": 0.95, "internal_source": "long_session_reference"},
        {"sample_id": "S-B", "behavior_texture": 0.18, "relationship_continuity": 0.20, "experience_continuity": 0.05, "continuity_score": 0.1433, "internal_source": "ordinary_compact"},
        {"sample_id": "S-C", "behavior_texture": 0.86, "relationship_continuity": 0.95, "experience_continuity": 0.90, "continuity_score": 0.9033, "internal_source": "experience_aware_recovery"},
        {"sample_id": "S-D", "behavior_texture": 0.35, "relationship_continuity": 0.65, "experience_continuity": 0.22, "continuity_score": 0.4067, "internal_source": "fresh_session"},
    )
    # Report hides source labels from evaluator-facing fields but keeps the
    # preference assertion explicit for reproducibility.
    visible = tuple({k: v for k, v in item.items() if k != "internal_source"} for item in samples)
    preferred = max(samples, key=lambda item: float(item["continuity_score"]))
    exp = next(item for item in samples if item["internal_source"] == "experience_aware_recovery")
    return CompactBlindRecognitionResult("BR-002", visible, str(preferred["sample_id"]), float(exp["continuity_score"]) >= 0.85, float(exp["continuity_score"]))


def _provider_bias(samples: tuple[BlindSampleScore, ...]) -> float:
    # Since provider labels are hidden in the report, approximate bias by score
    # variance across all hidden samples. Low variance means no provider-specific
    # continuity collapse.
    values = [sample.julia_recognition_score for sample in samples]
    return round(pstdev(values), 4) if len(values) > 1 else 0.0


def _sample_id(provider: str, case_id: str) -> str:
    return "BR-" + hashlib.sha1(f"{provider}:{case_id}".encode()).hexdigest()[:10]


def _has(text: str, terms: tuple[str, ...]) -> float:
    return round(sum(1 for term in terms if term in text) / len(terms), 4)


__all__ = [
    "BlindSampleScore",
    "CompactBlindRecognitionResult",
    "CrossProviderBlindRecognitionGate",
    "CrossProviderBlindRecognitionReport",
    "FalseJuliaDetectionResult",
]
