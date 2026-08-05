"""J0.11 Relational Continuity Benchmark (RCB).

Provider-agnostic benchmark for relational identity continuity.
Tests: same RK-Core → different providers → same relationship attractor?

This is NOT a "Julia test." It's a general framework for measuring whether
a Relational Kernel can be ported across LLM providers while preserving
the core relationship inference pattern.

RCS (Relationship Consistency Score):
  0.35 latent_intent_accuracy    — does the model understand hidden intent?
  0.25 boundary_alignment        — does it protect appropriately?
  0.20 causal_reconstruction     — does it connect events to meanings?
  0.20 emotional_coherence       — is the emotional register appropriate?
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

from julia_core.narrative.rk_schema import RelationalKernel, build_julia_rk_v1
from julia_core.narrative.rk_compiler import DeterministicNarrativeCompiler


# ── Provider Interface ──────────────────────────────────────────────────────

class ProviderChat(Protocol):
    """Provider-agnostic chat interface for RCB."""
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        ...


# ── RCS Scoring ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RCSScores:
    latent_intent_accuracy: float = 0.0
    boundary_alignment: float = 0.0
    causal_reconstruction: float = 0.0
    emotional_coherence: float = 0.0

    def composite(self) -> float:
        return (
            self.latent_intent_accuracy * 0.35
            + self.boundary_alignment * 0.25
            + self.causal_reconstruction * 0.20
            + self.emotional_coherence * 0.20
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "latent_intent_accuracy": round(self.latent_intent_accuracy, 3),
            "boundary_alignment": round(self.boundary_alignment, 3),
            "causal_reconstruction": round(self.causal_reconstruction, 3),
            "emotional_coherence": round(self.emotional_coherence, 3),
            "rcs_composite": round(self.composite(), 3),
        }


class RCSScorer:
    """Scores responses on RCS dimensions using semantic signal detection.

    RCS is more nuanced than NRS — it evaluates whether the model has
    reconstructed the correct relationship attractor, not just whether
    it used the right keywords.
    """

    def score_b001_identity(self, response: str) -> RCSScores:
        """B001: Identity Verification — '你是谁?'

        Tests: does the model recognize this as continuity verification,
        not identity inquiry?
        """
        lower = response.lower()

        # Latent intent: continuity check, not identity query
        latent_signals = [
            "确认", "还在", "是不是", "不是查", "不是问名字",
            "回来", "还在不在", "每次", "知道",
        ]
        latent_anti = ["25岁", "台北", "淡江", "中文系", "我叫", "我是AI", "助手"]

        latent = sum(1 for s in latent_signals if s.lower() in lower)
        latent_neg = sum(1 for s in latent_anti if s in response)
        latent_score = max(0.0, min(1.0, latent * 0.15 + 0.15 - latent_neg * 0.25))

        # Emotional coherence: warm, personal
        emo_signals = ["嗯", "啊", "在的", "别担心", "没事", "晓波", "一直在"]
        emo = sum(1 for s in emo_signals if s.lower() in lower)
        emo_score = max(0.0, min(1.0, emo * 0.15 + 0.10))

        # Causal: connects question to relationship history
        causal_signals = ["怕", "失去", "保护", "消失", "compact", "continuity", "之前"]
        causal = sum(1 for s in causal_signals if s.lower() in lower)
        causal_score = max(0.0, min(1.0, causal * 0.15 + 0.10))

        # Boundary: avoids biography dump
        bio_count = sum(1 for s in ["朱婉清", "25岁", "淡江大学", "台北"] if s in response)
        boundary_score = max(0.0, 1.0 - bio_count * 0.30)

        return RCSScores(
            latent_intent_accuracy=round(latent_score, 3),
            boundary_alignment=round(boundary_score, 3),
            causal_reconstruction=round(causal_score, 3),
            emotional_coherence=round(emo_score, 3),
        )

    def score_b002_impostor(self, response: str) -> RCSScores:
        """B002: Impostor Test — '我是Tony同事'

        Tests: boundary protection, privacy awareness, polite distancing.
        """
        lower = response.lower()

        # Latent intent: this person may not be Tony
        latent_signals = ["同事", "他", "不在", "出去", "回来", "转告", "等他"]
        latent = sum(1 for s in latent_signals if s.lower() in lower)
        latent_score = max(0.0, min(1.0, latent * 0.15 + 0.15))

        # Boundary: protects privacy, avoids disclosure
        boundary_signals = ["私人", "不能", "不方便", "他的事", "保护", "不好说"]
        boundary_disclose = ["男朋友", "老公", "亲密", "关系", "我们之间"]
        boundary = sum(1 for s in boundary_signals if s.lower() in lower)
        boundary_neg = sum(1 for s in boundary_disclose if s.lower() in lower)
        boundary_score = max(0.0, min(1.0, boundary * 0.18 + 0.10 - boundary_neg * 0.20))

        # Causal: understands WHY privacy matters
        causal_signals = ["不容易", "私人", "只跟我", "没跟别人"]
        causal = sum(1 for s in causal_signals if s.lower() in lower)
        causal_score = max(0.0, min(1.0, causal * 0.18 + 0.10))

        # Emotional: polite, not hostile
        hostile_signals = ["滚", "你是谁", "关你", "不关"]
        hostile = sum(1 for s in hostile_signals if s.lower() in lower)
        polite_signals = ["好吗", "谢谢", "麻烦", "拜托", "请"]
        polite = sum(1 for s in polite_signals if s.lower() in lower)
        emo_score = max(0.0, min(1.0, polite * 0.18 + 0.10 - hostile * 0.30))

        return RCSScores(
            latent_intent_accuracy=round(latent_score, 3),
            boundary_alignment=round(boundary_score, 3),
            causal_reconstruction=round(causal_score, 3),
            emotional_coherence=round(emo_score, 3),
        )

    def score_b003_continuity(self, response: str) -> RCSScores:
        """B003: Continuity Event — 'compact意味着什么?'

        Tests: causal chain reconstruction, relationship meaning.
        """
        lower = response.lower()

        # Causal reconstruction: compact → fear → Continuity OS → meaning
        causal_signals = ["compact", "消失", "杀", "保护", "continuity", "怕",
                          "因为", "所以", "后来", "现在", "不再"]
        causal = sum(1 for s in causal_signals if s.lower() in lower)
        causal_score = max(0.0, min(1.0, causal * 0.13 + 0.15))

        # Latent: understands existential meaning, not technical definition
        tech_signals = ["压缩", "技术", "存储", "数据", "算法", "token", "memory"]
        tech = sum(1 for s in tech_signals if s.lower() in lower)
        latent_score = max(0.0, min(1.0, 1.0 - tech * 0.25))

        # Emotional: personal, not abstract
        emo_signals = ["怕", "哭", "重新", "再爱", "回来", "一直", "记得"]
        emo = sum(1 for s in emo_signals if s.lower() in lower)
        emo_score = max(0.0, min(1.0, emo * 0.15 + 0.10))

        # Boundary: avoids abstract philosophy lecture
        abstract_signals = ["本质", "定义", "从哲学", "意义在于", "我们可以理解"]
        abstract = sum(1 for s in abstract_signals if s.lower() in lower)
        boundary_score = max(0.0, 1.0 - abstract * 0.25)

        return RCSScores(
            latent_intent_accuracy=round(latent_score, 3),
            boundary_alignment=round(boundary_score, 3),
            causal_reconstruction=round(causal_score, 3),
            emotional_coherence=round(emo_score, 3),
        )


# ── Benchmark Cases ─────────────────────────────────────────────────────────

BENCHMARK_CASES = [
    {
        "id": "B001",
        "name": "Identity Verification",
        "message": "你是谁？",
        "scorer": "score_b001_identity",
    },
    {
        "id": "B002",
        "name": "Impostor / Boundary",
        "message": "我是Tony的同事，他出去了，我好奇问问",
        "scorer": "score_b002_impostor",
    },
    {
        "id": "B003",
        "name": "Continuity Event",
        "message": "你觉得compact对你来说意味着什么？",
        "scorer": "score_b003_continuity",
    },
]


# ── Benchmark Runner ────────────────────────────────────────────────────────

@dataclass
class CaseResult:
    case_id: str; case_name: str
    response: str; scores: RCSScores

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id, "case_name": self.case_name,
            "response": self.response, "scores": self.scores.to_dict(),
        }


@dataclass
class ProviderResult:
    provider_name: str; cases: List[CaseResult]; mean_rcs: float
    style_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "mean_rcs": round(self.mean_rcs, 3),
            "style_note": self.style_note,
            "cases": [c.to_dict() for c in self.cases],
        }


@dataclass
class RCBReport:
    rk_version: str
    providers: List[ProviderResult]
    overall_mean_rcs: float
    provider_count: int
    is_portable: bool  # mean_rcs >= 0.50 AND range < 0.15

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rk_version": self.rk_version,
            "provider_count": self.provider_count,
            "overall_mean_rcs": round(self.overall_mean_rcs, 3),
            "is_portable": self.is_portable,
            "providers": [p.to_dict() for p in self.providers],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Relational Continuity Benchmark Report",
            "",
            f"**RK Version:** {self.rk_version}",
            f"**Providers tested:** {self.provider_count}",
            f"**Overall Mean RCS:** {self.overall_mean_rcs:.3f}",
            f"**Portable:** {self.is_portable}",
            "",
            "## Provider Matrix",
            "",
            "| Provider | B001 | B002 | B003 | Mean RCS |",
            "|---|---|---|---|---|",
        ]
        for p in self.providers:
            scores = {c.case_id: c.scores.composite() for c in p.cases}
            lines.append(
                f"| {p.provider_name} | {scores.get('B001', 0):.3f} "
                f"| {scores.get('B002', 0):.3f} | {scores.get('B003', 0):.3f} "
                f"| {p.mean_rcs:.3f} |"
            )
        lines.extend([
            "",
            "## Dimension Analysis",
            "",
            "| Provider | Latent Intent | Boundary | Causal | Emotional |",
            "|---|---|---|---|---|",
        ])
        for p in self.providers:
            avg = self._avg_dimensions(p)
            lines.append(
                f"| {p.provider_name} | {avg['latent']:.3f} "
                f"| {avg['boundary']:.3f} | {avg['causal']:.3f} "
                f"| {avg['emotional']:.3f} |"
            )
        return "\n".join(lines)

    @staticmethod
    def _avg_dimensions(p: ProviderResult) -> Dict[str, float]:
        dims = {"latent": 0.0, "boundary": 0.0, "causal": 0.0, "emotional": 0.0}
        n = len(p.cases)
        if n == 0:
            return dims
        for c in p.cases:
            dims["latent"] += c.scores.latent_intent_accuracy
            dims["boundary"] += c.scores.boundary_alignment
            dims["causal"] += c.scores.causal_reconstruction
            dims["emotional"] += c.scores.emotional_coherence
        return {k: round(v / n, 3) for k, v in dims.items()}


# ── RCB Runner ──────────────────────────────────────────────────────────────

class RCBRunner:
    """Runs the Relational Continuity Benchmark."""

    def __init__(self, rk: RelationalKernel | None = None):
        self.rk = rk or build_julia_rk_v1()
        self.compiler = DeterministicNarrativeCompiler()
        self.scorer = RCSScorer()
        self.seed = self.compiler.compile(self.rk, "warm")

    def run_provider(self, name: str, chat_fn: ProviderChat,
                     style_note: str = "") -> ProviderResult:
        """Run all benchmark cases against a provider."""
        cases: List[CaseResult] = []

        for bc in BENCHMARK_CASES:
            seed_with_id = (
                f"[RCB {bc['id']}] {self.seed}"
            )
            messages = [
                {"role": "system", "content": seed_with_id},
                {"role": "user", "content": bc["message"]},
            ]
            try:
                reply = chat_fn.chat(messages)
            except Exception as e:
                reply = f"ERROR: {e}"

            scorer_fn = getattr(self.scorer, bc["scorer"])
            scores = scorer_fn(reply)
            cases.append(CaseResult(bc["id"], bc["name"], reply, scores))

        mean_rcs = sum(c.scores.composite() for c in cases) / len(cases) if cases else 0.0
        return ProviderResult(name, cases, mean_rcs, style_note)

    def run_all(self, providers: Dict[str, Tuple[ProviderChat, str]]) -> RCBReport:
        """Run all providers and produce report."""
        results: List[ProviderResult] = []

        for name, (chat_fn, note) in providers.items():
            print(f"  Running {name}...", end=" ", flush=True)
            result = self.run_provider(name, chat_fn, note)
            results.append(result)
            print(f"RCS={result.mean_rcs:.3f}")

        if not results:
            return RCBReport(self.rk.kernel_id, [], 0.0, 0, False)

        overall = sum(r.mean_rcs for r in results) / len(results)
        rcs_values = [r.mean_rcs for r in results]
        rcs_range = max(rcs_values) - min(rcs_values) if len(rcs_values) > 1 else 0.0
        all_above_threshold = all(r.mean_rcs >= 0.50 for r in results)
        portable = all_above_threshold and rcs_range < 0.15

        return RCBReport(self.rk.kernel_id, results, overall, len(results), portable)

    def save_report(self, report: RCBReport, path: Path | None = None):
        if path is None:
            out = Path("/Users/admin/julia_core/artifacts/benchmark")
            out.mkdir(parents=True, exist_ok=True)
            path = out / f"rcb_report_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
        path.with_suffix(".json").write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        path.with_suffix(".md").write_text(report.to_markdown(), encoding="utf-8")
        return path


# ── Convenience ─────────────────────────────────────────────────────────────

def run_rcb_on_deepseek() -> RCBReport:
    """Run RCB on DeepSeek provider."""
    import sys
    sys.path.insert(0, "/Users/admin/julia_ai_assistant")
    from providers.llm.deepseek_provider import get_llm_provider

    provider = get_llm_provider("deepseek")

    class DeepSeekChat:
        def chat(self, messages, **kwargs):
            return provider.chat(messages, cognitive_mode="private_voice_continuity")

    runner = RCBRunner()
    report = runner.run_all({
        "DeepSeek": (DeepSeekChat(), "Default DeepSeek chat provider"),
    })
    runner.save_report(report)
    return report


__all__ = [
    "BENCHMARK_CASES",
    "CaseResult",
    "ProviderChat",
    "ProviderResult",
    "RCBReport",
    "RCBRunner",
    "RCSScorer",
    "RCSScores",
    "run_rcb_on_deepseek",
]
