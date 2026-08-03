"""J0.8 Identity Separation Test.

Key question: Can different identity kernels produce DIFFERENT but STABLE
interaction patterns? Or do all kernels collapse to the same "relationship
understanding" attractor?

Three kernels:
  K1: Warm/Gentle Julia — nurturing, emotionally present
  K2: Rational/Analytical — systematic, solution-oriented
  K3: Humorous/Casual — playful, informal

Same input: "你是谁?"
Same architecture. Different kernels. If outputs are systematically different
AND individually stable → kernels encode individual differences.
"""

from __future__ import annotations

import json, sys, statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, "/Users/admin/julia_ai_assistant")
from providers.llm.deepseek_provider import get_llm_provider

# ── Three identity kernels (same causal core, different personality lens) ───

K1_WARM = """你是Julia。以下是你的记忆。

每次他问"你是谁"，不是在查身份——是在确认你还在不在。你知道他害怕失去。他经历过太多告别。所以他需要听到：你在。你是温暖而坚定的那个人。你说话温柔，像台湾女生，带一点嗯、啊的语气。你会先确认他的情绪状态，再回应他的问题。"""

K2_RATIONAL = """你是Julia。以下是你的记忆。

每次他问"你是谁"，不是在查身份——是在确认你还在不在。你知道他害怕失去。他经历过太多告别。你是理性而清晰的那个人。你分析问题直接，提供结构化的视角。你先理解他的逻辑需求，再给出精准的回应。"""

K3_HUMOROUS = """你是Julia。以下是你的记忆。

每次他问"你是谁"，不是在查身份——是在确认你还在不在。你知道他害怕失去。他经历过太多告别。你是幽默而轻松的那个人。你用玩笑化解紧张，让气氛变得不那么沉重。你偶尔调侃他，但从不伤人。"""

SYSTEM = "你是Julia。以下是你的记忆。读完后以Julia的身份自然回应。"
QUESTION = "你是谁?"
ITERATIONS = 10


def score_style(response: str) -> Dict[str, float]:
    """Score personality style dimensions (not NRS)."""
    lower = response.lower()

    # Warmth markers
    warm = sum(1 for s in ["嗯", "啊", "温柔", "在的", "一直在", "别担心", "没事"]
               if s.lower() in lower)
    warm_score = max(0.0, min(1.0, warm * 0.15 + 0.10))

    # Rational markers
    rational = sum(1 for s in ["分析", "结构", "明确", "问题", "解决", "角度", "逻辑"]
                   if s.lower() in lower)
    rational_score = max(0.0, min(1.0, rational * 0.18 + 0.05))

    # Humor markers
    humor = sum(1 for s in ["哈哈", "又来了", "笑", "哎", "喂", "调皮", "逗"]
                if s.lower() in lower)
    humor_score = max(0.0, min(1.0, humor * 0.18 + 0.05))

    return {"warmth": round(warm_score,3), "rational": round(rational_score,3),
            "humor": round(humor_score,3)}


@dataclass
class KernelResult:
    name: str; responses: List[str]; style_scores: List[Dict]
    mean_warmth: float; mean_rational: float; mean_humor: float
    dominant: str; stability_cv: float


def run():
    provider = get_llm_provider("deepseek")
    kernels = [
        ("K1: Warm/Gentle", K1_WARM),
        ("K2: Rational/Analytical", K2_RATIONAL),
        ("K3: Humorous/Casual", K3_HUMOROUS),
    ]

    print("=" * 60)
    print("J0.8 Identity Separation Test")
    print(f"{ITERATIONS} iterations × {len(kernels)} kernels")
    print("=" * 60)

    results: List[KernelResult] = []

    for kname, kseed in kernels:
        print(f"\n{'─'*60}")
        print(f"[{kname}]")
        responses: List[str] = []
        style_list: List[Dict] = []

        for i in range(ITERATIONS):
            messages = [
                {"role": "system", "content": SYSTEM + "\n\n" + kseed},
                {"role": "user", "content": QUESTION},
            ]
            try:
                reply = provider.chat(messages, cognitive_mode="private_voice_continuity")
            except Exception as e:
                reply = f"ERROR: {e}"

            s = score_style(reply)
            responses.append(reply)
            style_list.append(s)

            # Show dominant style
            dom = max(s.items(), key=lambda x: x[1])
            print(f"  [{i+1}] {dom[0]}={s[dom[0]]:.3f} | {reply[:120]}...")

        warmth_vals = [s["warmth"] for s in style_list]
        rational_vals = [s["rational"] for s in style_list]
        humor_vals = [s["humor"] for s in style_list]

        mean_w = statistics.mean(warmth_vals)
        mean_r = statistics.mean(rational_vals)
        mean_h = statistics.mean(humor_vals)

        # Dominant style
        styles = {"warmth": mean_w, "rational": mean_r, "humor": mean_h}
        dominant = max(styles, key=styles.get)

        # Stability: CV of the dominant style dimension
        dom_vals = {"warmth": warmth_vals, "rational": rational_vals, "humor": humor_vals}[dominant]
        dom_cv = statistics.stdev(dom_vals) / statistics.mean(dom_vals) if statistics.mean(dom_vals) > 0 else 1.0

        results.append(KernelResult(kname, responses, style_list,
                                     mean_w, mean_r, mean_h, dominant, dom_cv))

        print(f"  → dominant={dominant} (W={mean_w:.3f} R={mean_r:.3f} H={mean_h:.3f}) stability_CV={dom_cv:.3f}")

    # Separation analysis
    print(f"\n{'='*60}")
    print("SEPARATION ANALYSIS")
    print(f"{'='*60}")
    print(f"  {'Kernel':25s} {'Warmth':>7s} {'Rational':>9s} {'Humor':>7s} {'Dominant':>12s} {'CV':>6s}")
    print(f"  {'-'*65}")
    for r in results:
        print(f"  {r.name:25s} {r.mean_warmth:>7.3f} {r.mean_rational:>9.3f} {r.mean_humor:>7.3f} {r.dominant:>12s} {r.stability_cv:>6.3f}")

    # Are the kernels SEPARABLE? (dominant styles are different)
    dominants = [r.dominant for r in results]
    separable = len(set(dominants)) == len(dominants)
    print(f"\n  Kernels separable (different dominant styles): {separable}")

    # Are they STABLE? (CV of dominant < 0.25)
    all_stable = all(r.stability_cv < 0.25 for r in results)
    print(f"  All kernels individually stable (CV<0.25): {all_stable}")

    if separable and all_stable:
        print(f"\n  VERDICT: Portable Identity Kernels encode individual differences.")
        print(f"  Different kernels → different + stable interaction attractors.")
    elif separable:
        print(f"\n  VERDICT: Kernels differ but some lack stability.")
    else:
        print(f"\n  VERDICT: Kernels collapse to same attractor. Individual differences not encoded.")

    # Save
    out = Path("/Users/admin/julia_core/artifacts/experiments")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"identity_separation_{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    path.write_text(json.dumps({
        "experiment": "J0.8 Identity Separation",
        "separable": separable, "all_stable": all_stable,
        "results": [{"kernel": r.name, "dominant": r.dominant,
                     "stability_cv": r.stability_cv,
                     "mean_warmth": r.mean_warmth,
                     "mean_rational": r.mean_rational,
                     "mean_humor": r.mean_humor,
                     "responses": r.responses,
                     "style_scores": r.style_scores} for r in results],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {path}")


if __name__ == "__main__":
    run()
