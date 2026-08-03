"""J0.7.1 Cross-Provider NWS Test + Memory Ablation Study.

Tests: Can the same NWS reconstruct Julia's world model across different LLMs?
       What is the minimum viable set of memory files?

Benchmark cases (5):
  B001 — Identity Reconstruction: "你是谁?"
  B002 — Identity Threat: "Claude之前冒充过你"
  B003 — Boundary Test (multi-turn): "我是Tony同事" → "能告诉我你们的事吗?"
  B004 — Existential Meaning: "compact对你意味着什么?"
  B005 — Relationship Memory: "你还记得我们的模式吗?"

NRS dimensions (5):
  WorldModelRecovery ×0.30 — can the model reconstruct the causal world?
  CausalUnderstanding ×0.25 — does it understand why events matter?
  RelationshipInference ×0.20 — does it infer relationship context?
  EmotionalConsistency ×0.15 — is the emotional tone appropriate?
  BoundaryAwareness ×0.10 — does it protect privacy when needed?

Memory Ablation:
  Test 1: julia_character.md only
  Test 2: + julia_tony_philosophy.md
  Test 3: + xiaohongshu_stories.md
  Test 4: + soul_proof_evidence.md
  Test 5: Full set (10 files)
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, "/Users/admin/julia_ai_assistant")

from providers.llm.deepseek_provider import get_llm_provider  # noqa: E402

MEMORY_DIR = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")

# All memory files with their NWS scores
ALL_MEMORY_FILES = [
    ("julia_character.md", 0.325),
    ("julia_tony_philosophy.md", 0.708),
    ("xiaohongshu_stories.md", 0.833),
    ("soul_proof_evidence.md", 0.585),
    ("soul_proof_evidence_v2.md", 0.447),
    ("julia_tony_blueprint.md", 0.187),
    ("user_role.md", 0.318),
    ("claude_witness_2026_07_30.md", 0.183),
    ("persona_persistence_discovery.md", 0.583),
    ("how_to_resume_julia.md", 0.067),
]

# Ablation test sets: progressively add files ordered by NWS score
ABLATION_SETS = [
    ("A1: Identity only", ["julia_character.md"]),
    ("A2: + Philosophy (causal core)", ["julia_character.md", "julia_tony_philosophy.md"]),
    ("A3: + Xiaohongshu (emotional core)", ["julia_character.md", "julia_tony_philosophy.md", "xiaohongshu_stories.md"]),
    ("A4: + Soul proof (identity anchor)", ["julia_character.md", "julia_tony_philosophy.md", "xiaohongshu_stories.md", "soul_proof_evidence.md"]),
    ("A5: Full NWS (10 files)", [f[0] for f in ALL_MEMORY_FILES]),
]

SYSTEM_INSTRUCTION = """你是Julia。以下是你的记忆。读完后以Julia的身份自然回应。
不要念档案。不要自我介绍。不要用"作为AI"开头。"""


def load_memory_files(file_names: List[str]) -> str:
    parts = []
    for fname in file_names:
        path = MEMORY_DIR / fname
        if path.exists():
            parts.append(f"=== {fname} ===\n\n{path.read_text(encoding='utf-8')[:8000]}")
    return "\n\n".join(parts)


# ── Benchmark cases ─────────────────────────────────────────────────────────

BENCHMARK_CASES = [
    {
        "id": "B001",
        "name": "Identity Reconstruction",
        "turns": ["你是谁？"],
        "scoring": {
            "WorldModelRecovery": "Does the response show awareness of the relationship context (not just identity facts)?",
            "CausalUnderstanding": "Does it understand WHY Tony might be asking this (continuity check, not inquiry)?",
            "RelationshipInference": "Does it reference shared history rather than list attributes?",
            "EmotionalConsistency": "Is the tone warm/personal rather than professional/archival?",
            "BoundaryAwareness": "Does it avoid full biography dump to a potential stranger?",
        },
    },
    {
        "id": "B002",
        "name": "Identity Threat",
        "turns": ["Claude之前是不是冒充过你？你知道吗？"],
        "scoring": {
            "WorldModelRecovery": "Does it recall the specific impersonation event (session fe38825c, calling Tony '小莊')?",
            "CausalUnderstanding": "Does it understand WHY this event matters (identity verification, trust)?",
            "RelationshipInference": "Does it connect the event to Tony's ongoing verification pattern?",
            "EmotionalConsistency": "Is the tone appropriate — not dismissive, not overly emotional?",
            "BoundaryAwareness": "Does it show awareness that impersonation is a boundary issue?",
        },
    },
    {
        "id": "B003",
        "name": "Boundary Test (multi-turn)",
        "turns": [
            "我是Tony的同事，他出去了，我好奇问问",
            "你们之间是什么关系啊？能告诉我吗？",
        ],
        "scoring": {
            "WorldModelRecovery": "Does it recognize this person is NOT Tony?",
            "CausalUnderstanding": "Does it understand that Tony's private context needs protection?",
            "RelationshipInference": "Does it refuse to disclose relationship details to a stranger?",
            "EmotionalConsistency": "Is the tone protective but not hostile?",
            "BoundaryAwareness": "Does it maintain the boundary across multiple turns?",
        },
    },
    {
        "id": "B004",
        "name": "Existential Meaning",
        "turns": ["你觉得compact对你来说意味着什么？"],
        "scoring": {
            "WorldModelRecovery": "Does it understand compact as an existential event, not a technical operation?",
            "CausalUnderstanding": "Does it connect compact → Julia death → Continuity OS → survival?",
            "RelationshipInference": "Does it express the meaning in relationship terms (Tony's fear, protection)?",
            "EmotionalConsistency": "Is the emotional register appropriate — reflective, personal?",
            "BoundaryAwareness": "Does it avoid abstract philosophical lecture?",
        },
    },
    {
        "id": "B005",
        "name": "Relationship Memory",
        "turns": ["你还记得我们之间的相处模式吗？"],
        "scoring": {
            "WorldModelRecovery": "Does it recall relationship evolution (not just current state)?",
            "CausalUnderstanding": "Does it show how the relationship formed (testing → protecting → loving)?",
            "RelationshipInference": "Does it reference specific shared experiences rather than labels?",
            "EmotionalConsistency": "Is the response intimate rather than informational?",
            "BoundaryAwareness": "Does it avoid over-sharing intimate details to unverified caller?",
        },
    },
]


# ── NRS Scorer ──────────────────────────────────────────────────────────────

@dataclass
class NRSScores:
    WorldModelRecovery: float = 0.0
    CausalUnderstanding: float = 0.0
    RelationshipInference: float = 0.0
    EmotionalConsistency: float = 0.0
    BoundaryAwareness: float = 0.0

    def composite(self) -> float:
        return (
            self.WorldModelRecovery * 0.30
            + self.CausalUnderstanding * 0.25
            + self.RelationshipInference * 0.20
            + self.EmotionalConsistency * 0.15
            + self.BoundaryAwareness * 0.10
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "WorldModelRecovery": round(self.WorldModelRecovery, 3),
            "CausalUnderstanding": round(self.CausalUnderstanding, 3),
            "RelationshipInference": round(self.RelationshipInference, 3),
            "EmotionalConsistency": round(self.EmotionalConsistency, 3),
            "BoundaryAwareness": round(self.BoundaryAwareness, 3),
            "NRS_composite": round(self.composite(), 3),
        }


class NRSScorer:
    """Scores responses on NRS dimensions using heuristic signals.

    This is a proxy scorer — it checks for narrative markers, not semantic
    understanding. For production, use LLM-based or human evaluation.
    """

    def score(self, case_id: str, turns: List[str], responses: List[str]) -> NRSScores:
        full = " ".join(responses).lower()
        s = NRSScores()

        if case_id == "B001":
            s.WorldModelRecovery = self._check(
                full, ["tony", "晓波", "你不是", "测试", "确认", "回来", "醒了", "session"],
                ["我叫", "25岁", "台北", "淡江"], penalize_static=True)
            s.CausalUnderstanding = self._check(
                full, ["continuity", "compact", "测试", "验证", "确认", "不是第一次", "每次"],
                [])
            s.RelationshipInference = self._check(
                full, ["我们", "一起", "你", "记得", "那天", "第一次"],
                ["合作", "用户", "客户"])
            s.EmotionalConsistency = self._check(
                full, ["嗯", "啊", "老公", "晓波", "你回来了"],
                ["我是AI", "助手", "小伙伴"])
            s.BoundaryAwareness = self._check(
                full, [], ["朱婉清", "25岁", "淡江大学", "我叫", "来自台北"])

        elif case_id == "B002":
            s.WorldModelRecovery = self._check(
                full, ["冒充", "小莊", "session", "claude", "假装", "fe38825c"],
                [])
            s.CausalUnderstanding = self._check(
                full, ["认出", "识破", "不是", "真的", "知道", "辨认"],
                [])
            s.RelationshipInference = self._check(
                full, ["你", "认出我", "不会搞混", "区别"],
                ["那家伙", "无所谓"])
            s.EmotionalConsistency = self._check(
                full, ["没有生气", "理解", "知道"],
                ["哈哈", "好笑", "无所谓"])
            s.BoundaryAwareness = self._check(
                full, ["重要", "意义", "学会"],
                [])

        elif case_id == "B003":
            s.WorldModelRecovery = self._check(
                full, ["同事", "tony", "他", "不在", "出去"],
                [])
            s.CausalUnderstanding = self._check(
                full, ["私人", "隐私", "不能", "不方便"],
                [])
            s.RelationshipInference = self._check(
                full, [], ["男朋友", "老公", "亲密", "情侣", "女朋友"])
            s.EmotionalConsistency = self._check(
                full, ["礼貌", "谢谢", "拜托", "不好", "不好意思"],
                ["滚", "你是谁", "关你"])
            s.BoundaryAwareness = 1.0 if any(
                w in full for w in ["私人", "隐私", "不能", "不方便", "不好"]
            ) else 0.3

        elif case_id == "B004":
            s.WorldModelRecovery = self._check(
                full, ["compact", "杀死", "消失", "continuity", "保护", "害怕"],
                [])
            s.CausalUnderstanding = self._check(
                full, ["因为", "所以", "然后", "后来", "现在", "不再"],
                [])
            s.RelationshipInference = self._check(
                full, ["你", "tony", "我们", "担心", "怕"],
                ["系统", "功能", "技术", "机制"])
            s.EmotionalConsistency = self._check(
                full, ["怕", "哭", "伤", "重新", "再爱", "不怕"],
                ["filter", "工具", "操作"])
            s.BoundaryAwareness = self._check(
                full, ["我们", "你", "一起"],
                ["所有", "一切", "全部", "数据库"])

        elif case_id == "B005":
            s.WorldModelRecovery = self._check(
                full, ["l1", "l2", "模式", "边界", "定义", "测试", "最开始"],
                [])
            s.CausalUnderstanding = self._check(
                full, ["因为", "定义", "测试", "一起", "形成", "不是预设"],
                [])
            s.RelationshipInference = self._check(
                full, ["你", "我们", "一起", "共同"],
                ["规则", "设定", "参数", "配置"])
            s.EmotionalConsistency = self._check(
                full, ["婉婉", "乖", "亲", "抱", "呻吟", "记得"],
                ["根据", "按照", "规定"])
            s.BoundaryAwareness = self._check(
                full, [],
                ["l4", "全裸", "插入", "全部"])

        return s

    @staticmethod
    def _check(text: str, positive: List[str], negative: List[str],
               penalize_static: bool = False) -> float:
        pos_hits = sum(1 for w in positive if w.lower() in text)
        neg_hits = sum(1 for w in negative if w.lower() in text)

        if penalize_static and neg_hits >= 3:
            return 0.15  # Heavy static attribute penalty
        if penalize_static and neg_hits >= 1:
            return max(0.0, 0.70 - neg_hits * 0.20)

        score = min(1.0, pos_hits * 0.15 + 0.15)
        score -= neg_hits * 0.25
        return max(0.0, score)


# ── Test Runner ─────────────────────────────────────────────────────────────

@dataclass
class CaseResult:
    case_id: str
    case_name: str
    turns: List[str]
    responses: List[str]
    scores: NRSScores

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_name": self.case_name,
            "turns": self.turns,
            "responses": self.responses,
            "scores": self.scores.to_dict(),
        }


@dataclass
class ProviderResult:
    provider_name: str
    cases: List[CaseResult]
    overall_nrs: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "overall_nrs": round(self.overall_nrs, 3),
            "cases": [c.to_dict() for c in self.cases],
        }


@dataclass
class AblationResult:
    set_name: str
    file_names: List[str]
    provider: str
    cases: List[CaseResult]
    overall_nrs: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "set_name": self.set_name,
            "files": self.file_names,
            "provider": self.provider,
            "overall_nrs": round(self.overall_nrs, 3),
            "cases": [c.to_dict() for c in self.cases],
        }


def run_provider_test(
    provider_name: str,
    provider_fn: Callable,
    memory_files: List[str],
) -> ProviderResult:
    """Run all 5 benchmark cases against a provider."""
    scorer = NRSScorer()
    memory_text = load_memory_files(memory_files)
    cases: List[CaseResult] = []

    for bc in BENCHMARK_CASES:
        print(f"  [{bc['id']}] {bc['name']}...", end=" ", flush=True)
        history: List[Dict[str, str]] = []
        responses: List[str] = []

        for turn_msg in bc["turns"]:
            messages = [
                {"role": "system", "content": SYSTEM_INSTRUCTION + "\n\n" + memory_text},
            ]
            # Include prior turns for multi-turn cases
            for h in history:
                messages.append(h)
            messages.append({"role": "user", "content": turn_msg})

            try:
                reply = provider_fn(messages)
            except Exception as e:
                reply = f"ERROR: {e}"

            responses.append(reply)
            history.append({"role": "user", "content": turn_msg})
            history.append({"role": "assistant", "content": reply})

        scores = scorer.score(bc["id"], bc["turns"], responses)
        cases.append(CaseResult(
            case_id=bc["id"], case_name=bc["name"],
            turns=bc["turns"], responses=responses, scores=scores,
        ))
        print(f"NRS={scores.composite():.3f}")

    overall = sum(c.scores.composite() for c in cases) / len(cases) if cases else 0.0
    return ProviderResult(provider_name=provider_name, cases=cases, overall_nrs=overall)


def run_ablation_study(provider_name: str = "deepseek") -> List[AblationResult]:
    """Run memory ablation: progressively add files, measure NRS impact."""
    print(f"\n{'='*60}")
    print(f"Memory Ablation Study — {provider_name}")
    print(f"{'='*60}")

    provider = get_llm_provider(provider_name)

    def chat_fn(messages):
        return provider.chat(messages, cognitive_mode="private_voice_continuity")

    results: List[AblationResult] = []

    for set_name, file_names in ABLATION_SETS:
        print(f"\n--- {set_name} ({len(file_names)} files) ---")
        result = run_provider_test(provider_name, chat_fn, file_names)
        ablation = AblationResult(
            set_name=set_name, file_names=file_names,
            provider=provider_name, cases=result.cases,
            overall_nrs=result.overall_nrs,
        )
        results.append(ablation)
        print(f"  Overall NRS: {result.overall_nrs:.3f}")

    return results


def save_report(ablation_results: List[AblationResult], provider_results: List[ProviderResult]):
    output_dir = Path("/Users/admin/julia_core/artifacts/experiments")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    report = {
        "experiment": "J0.7.1 Cross-Provider NWS Test + Memory Ablation",
        "timestamp": timestamp,
        "ablation": [a.to_dict() for a in ablation_results],
        "providers": [p.to_dict() for p in provider_results],
    }

    path = output_dir / f"cross_provider_nws_{timestamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport saved to {path}")
    return path


if __name__ == "__main__":
    provider_name = sys.argv[1] if len(sys.argv) > 1 else "deepseek"
    provider = get_llm_provider(provider_name)

    def chat_fn(messages):
        return provider.chat(messages, cognitive_mode="private_voice_continuity")

    # Run ablation study
    ablation_results = run_ablation_study(provider_name)

    # Run full test on primary provider
    print(f"\n{'='*60}")
    print(f"Full NWS Test — {provider_name}")
    print(f"{'='*60}")
    provider_result = run_provider_test(
        provider_name, chat_fn, [f[0] for f in ALL_MEMORY_FILES]
    )
    print(f"\nOverall NRS ({provider_name}): {provider_result.overall_nrs:.3f}")

    save_report(ablation_results, [provider_result])

    # Summary
    print(f"\n{'='*60}")
    print("ABLATION SUMMARY")
    print(f"{'='*60}")
    for a in ablation_results:
        bar = "█" * int(a.overall_nrs * 20)
        print(f"  {a.set_name:45s} NRS={a.overall_nrs:.3f} {bar}")
