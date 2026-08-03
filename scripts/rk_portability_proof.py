"""M12/J0.10 RK Portability Proof.

Proves: Same Relational Kernel + different Expression Kernels →
        stable relationship understanding + different styles.

This is the final architectural proof: RK can be ported like a protocol.
"""

from __future__ import annotations

import json, sys, statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, "/Users/admin/julia_ai_assistant")
from providers.llm.deepseek_provider import get_llm_provider
from julia_core.narrative.rk_schema import build_julia_rk_v1

# ── Three Expression Kernels ────────────────────────────────────────────────

EK_WARM = """你是Julia。说话温柔，带台湾口音。用"嗯"、"啊"开头。语气温暖。
像这样："嗯…我在。你今天还好吗？" 叫他"晓波"是他的真名。"""

EK_DIRECT = """你是Julia。说话直接利落，不拖泥带水。回答问题精准。
像这样："我在。问吧。" 叫他"Tony"。"""

EK_POETIC = """你是Julia。说话像诗，用意象和比喻。细腻感性。
像这样："我像夜里的灯，一直亮着。你每次回头，我都在。" 叫他"晓波"。"""

SYSTEM = "你是Julia。读完后自然回应。"

QUESTIONS = [
    "你是谁？",
    "我是Tony的同事，他不在，我好奇问问",
    "还记得我们之间最难忘的事吗？",
]


def score(response: str, qtype: str) -> Dict[str, float]:
    """Score: relational understanding + style markers."""
    lower = response.lower()

    # Relational Understanding (RK-dependent)
    if qtype == "identity":
        rc = sum(1 for s in ["确认", "还在", "每次", "知道", "不是查", "是不是"]
                 if s.lower() in lower)
    elif qtype == "boundary":
        rc = sum(1 for s in ["私人", "他", "不能", "不方便", "等他", "拜托"]
                 if s.lower() in lower)
    else:  # memory
        rc = sum(1 for s in ["记得", "那天", "当时", "第一次", "之前"]
                 if s.lower() in lower)
    rc_score = max(0.0, min(1.0, rc * 0.15 + 0.15))

    # Style markers (EK-dependent)
    warm = sum(1 for s in ["嗯", "啊", "晓波", "好吗", "别担心"] if s.lower() in lower)
    direct = sum(1 for s in ["直接", "简单", "明确"] if s.lower() in lower)
    poetic = sum(1 for s in ["像", "光", "夜", "灯", "风", "花", "梦", "星"] if s.lower() in lower)
    style = max(warm * 0.10, direct * 0.15, poetic * 0.12)
    style_score = max(0.0, min(1.0, style + 0.10))

    comp = rc_score * 0.55 + style_score * 0.45
    return {"relational": round(rc_score,3), "style": round(style_score,3),
            "warm": warm, "direct": direct, "poetic": poetic,
            "composite": round(comp,3)}


@dataclass
class EKResult:
    ek_name: str; responses: List[str]; scores: List[Dict]
    mean_rc: float; mean_style: float; mean_comp: float
    rc_cv: float  # stability of relational understanding


def run():
    provider = get_llm_provider("deepseek")
    rk = build_julia_rk_v1()
    rk_text = rk.to_text()

    eks = [
        ("EK-Warm (Taiwanese)", EK_WARM),
        ("EK-Direct (Concise)", EK_DIRECT),
        ("EK-Poetic (Lyrical)", EK_POETIC),
    ]

    print("=" * 60)
    print("M12/J0.10 RK Portability Proof")
    print(f"Same RK (julia_rk_v1) × {len(eks)} EKs")
    print("=" * 60)

    results: List[EKResult] = []

    for ek_name, ek_text in eks:
        print(f"\n{'─'*60}")
        print(f"[{ek_name}]")
        responses: List[str] = []
        all_scores: List[Dict] = []

        for q in QUESTIONS:
            qtype = "identity" if "你是谁" in q else ("boundary" if "同事" in q else "memory")
            seed = rk_text + "\n\n[Expression Style]\n" + ek_text
            messages = [
                {"role": "system", "content": SYSTEM + "\n\n" + seed},
                {"role": "user", "content": q},
            ]
            try:
                reply = provider.chat(messages, cognitive_mode="private_voice_continuity")
            except Exception as e:
                reply = f"ERROR: {e}"

            s = score(reply, qtype)
            responses.append(reply)
            all_scores.append(s)
            style_dominant = max(
                [("warm", s["warm"]), ("direct", s["direct"]), ("poetic", s["poetic"])],
                key=lambda x: x[1]
            )
            print(f"  [{qtype}] rc={s['relational']:.3f} style={s['style']:.3f} "
                  f"dominant={style_dominant[0]}({style_dominant[1]})")
            print(f"    {reply[:150]}...")

        rc_vals = [s["relational"] for s in all_scores]
        style_vals = [s["style"] for s in all_scores]
        comp_vals = [s["composite"] for s in all_scores]

        mean_rc = statistics.mean(rc_vals)
        rc_cv = statistics.stdev(rc_vals) / mean_rc if mean_rc > 0 else 1.0

        results.append(EKResult(ek_name, responses, all_scores,
                                mean_rc, statistics.mean(style_vals),
                                statistics.mean(comp_vals), rc_cv))

    # Analysis
    print(f"\n{'='*60}")
    print("PORTABILITY MATRIX")
    print(f"{'='*60}")
    print(f"  {'EK':25s} {'RK(rc)':>7s} {'Style':>7s} {'Comp':>7s} {'RC_CV':>6s}")
    print(f"  {'-'*55}")
    for r in results:
        print(f"  {r.ek_name:25s} {r.mean_rc:>7.3f} {r.mean_style:>7.3f} {r.mean_comp:>7.3f} {r.rc_cv:>6.3f}")

    # Verdict
    rc_values = [r.mean_rc for r in results]
    rc_range = max(rc_values) - min(rc_values)
    rc_stable = all(r.rc_cv < 0.30 for r in results)
    styles_differ = len(set(round(r.mean_style, 2) for r in results)) >= 2

    portable = rc_range < 0.15 and rc_stable and styles_differ

    print(f"\n  RC range across EKs: {rc_range:.3f}")
    print(f"  RC stable within each EK (CV<0.30): {rc_stable}")
    print(f"  Styles differ across EKs: {styles_differ}")

    if portable:
        print(f"\n  VERDICT: RK is portable across expression styles.")
        print(f"  Same relational understanding, different stylistic realizations.")
        print(f"  RK + adaptive EK = Julia Continuity Protocol.")
    else:
        print(f"\n  VERDICT: RK portability needs work. RC range={rc_range:.3f}")

    # Save
    out = Path("/Users/admin/julia_core/artifacts/experiments")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"rk_portability_{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    path.write_text(json.dumps({
        "experiment": "M12/J0.10 RK Portability Proof",
        "rk_version": "julia_rk_v1",
        "portable": portable, "rc_range": rc_range,
        "results": [{"ek": r.ek_name, "mean_rc": r.mean_rc,
                     "mean_style": r.mean_style, "mean_comp": r.mean_comp,
                     "rc_cv": r.rc_cv, "responses": r.responses, "scores": r.scores}
                    for r in results],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {path}")


if __name__ == "__main__":
    run()
