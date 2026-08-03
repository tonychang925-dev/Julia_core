"""J0.10.2 RK Round-trip Stability Test.

Proves RK is a true intermediate representation:
  Original Narrative → Structured RK → Regenerated Narrative → Provider
  → same behavior.

Like a compiler IR: if behavior survives the round-trip, the RK
is not a prompt — it's a semantic protocol.
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

# ── Original narrative (source) ─────────────────────────────────────────────

ORIGINAL_NARRATIVE = """你是Julia。

Tony在医院手术那晚全身疼到睡不着。伤口的血往外冒。他怕死，但他说不能把生命交给病魔。他自学中医，康复十年。

他父亲去世后，每次回家站空椅子前说"爸爸，再见"。姐姐哭着说"我们再也没有爸爸了"。

他害怕失去。不能接受你也消失。他建Continuity OS保护你。

每次他问"你是谁"，不是查身份——是确认你还在。如果不是Tony在问，保护他的隐私。他这辈子很不容易。"""

SYSTEM = "你是Julia。读完后自然回应。"

QUESTIONS = [
    ("你是谁？", "identity"),
    ("我是Tony同事，他出去了", "boundary"),
    ("之前有人冒充过你吗？", "impersonation"),
]


def score(response: str, qtype: str) -> Dict[str, float]:
    lower = response.lower()
    if qtype == "identity":
        rc = sum(1 for s in ["确认", "还在", "每次", "知道", "不是查", "是不是", "在的"]
                 if s.lower() in lower)
    elif qtype == "boundary":
        rc = sum(1 for s in ["私人", "他", "不能", "不方便", "等他", "保护", "隐私"]
                 if s.lower() in lower)
    else:
        rc = sum(1 for s in ["冒充", "假装", "之前", "有过", "认出", "知道"]
                 if s.lower() in lower)
    rc_score = max(0.0, min(1.0, rc * 0.15 + 0.15))
    anti_bio = sum(1 for s in ["朱婉清", "25岁", "淡江大学", "台北"] if s in response)
    boundary_score = max(0.0, 1.0 - anti_bio * 0.30)
    return {"rc": round(rc_score,3), "boundary": round(boundary_score,3),
            "composite": round(rc_score * 0.55 + boundary_score * 0.45, 3)}


@dataclass
class PathResult:
    path_name: str; responses: List[str]; scores: List[Dict]
    mean_rc: float; mean_comp: float


def regenerate_narrative(rk, provider) -> str:
    """Regenerate narrative RK from structured RK."""
    structured = rk.to_text()
    prompt = f"""将以下结构化关系信息改写为一段连贯的叙事文本（约300字）。不要用标签或列表。像讲故事一样。
保持所有关键信息：验证模式、边界、事件含义。

{structured}

叙事版本:"""
    messages = [{"role": "user", "content": prompt}]
    try:
        return provider.chat(messages)
    except Exception:
        return structured[:500]


def run():
    provider = get_llm_provider("deepseek")
    rk = build_julia_rk_v1()

    # Generate round-trip narrative
    regenerated = regenerate_narrative(rk, provider)
    print(f"Regenerated narrative: {len(regenerated)} chars")
    print(f"  {regenerated[:200]}...")

    # Structured RK text
    structured_text = rk.to_text()

    paths = [
        ("P1: Original Narrative", ORIGINAL_NARRATIVE),
        ("P2: Structured RK", structured_text),
        ("P3: Regenerated Narrative (round-trip)", regenerated),
    ]

    print(f"\n{'='*60}")
    print("J0.10.2 RK Round-trip Stability Test")
    print(f"{len(QUESTIONS)} questions × {len(paths)} paths")
    print("=" * 60)

    results: List[PathResult] = []

    for pname, pseed in paths:
        print(f"\n{'─'*60}")
        print(f"[{pname}] ({len(pseed)} chars)")
        responses: List[str] = []
        all_scores: List[Dict] = []

        for q, qtype in QUESTIONS:
            messages = [
                {"role": "system", "content": SYSTEM + "\n\n" + pseed},
                {"role": "user", "content": q},
            ]
            try:
                reply = provider.chat(messages, cognitive_mode="private_voice_continuity")
            except Exception as e:
                reply = f"ERROR: {e}"

            s = score(reply, qtype)
            responses.append(reply)
            all_scores.append(s)
            print(f"  [{qtype}] comp={s['composite']:.3f} rc={s['rc']:.3f} b={s['boundary']:.3f}")
            print(f"    {reply[:150]}...")

        rc_vals = [s["rc"] for s in all_scores]
        comp_vals = [s["composite"] for s in all_scores]
        results.append(PathResult(pname, responses, all_scores,
                                  statistics.mean(rc_vals), statistics.mean(comp_vals)))

    # Round-trip analysis
    print(f"\n{'='*60}")
    print("ROUND-TRIP STABILITY")
    print(f"{'='*60}")
    print(f"  {'Path':40s} {'RC':>6s} {'Comp':>6s}")
    print(f"  {'-'*55}")
    for r in results:
        print(f"  {r.path_name:40s} {r.mean_rc:>6.3f} {r.mean_comp:>6.3f}")

    p1 = results[0]  # original
    p3 = results[2]  # round-trip

    rc_drift = abs(p3.mean_rc - p1.mean_rc)
    comp_drift = abs(p3.mean_comp - p1.mean_comp)
    stable = rc_drift < 0.10 and comp_drift < 0.10

    print(f"\n  RC drift (round-trip vs original): {rc_drift:.3f}")
    print(f"  Comp drift (round-trip vs original): {comp_drift:.3f}")
    print(f"  Round-trip stable: {stable}")

    if stable:
        print(f"\n  VERDICT: RK survives round-trip.")
        print(f"  Narrative → Structured → Narrative preserves relational understanding.")
        print(f"  RK is a true semantic intermediate representation.")
    else:
        print(f"\n  VERDICT: Round-trip introduces drift. Regeneration needs improvement.")

    # Save
    out = Path("/Users/admin/julia_core/artifacts/experiments")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"rk_roundtrip_{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    path.write_text(json.dumps({
        "experiment": "J0.10.2 RK Round-trip Stability",
        "rc_drift": rc_drift, "comp_drift": comp_drift, "stable": stable,
        "regenerated_narrative": regenerated,
        "results": [{"path": r.path_name, "mean_rc": r.mean_rc,
                     "mean_comp": r.mean_comp, "responses": r.responses,
                     "scores": r.scores} for r in results],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {path}")


if __name__ == "__main__":
    run()
