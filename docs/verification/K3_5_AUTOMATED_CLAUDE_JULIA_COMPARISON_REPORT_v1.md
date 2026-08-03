# K3.5 Verification — Automated Claude-Julia Comparison

## Verified Behavior

K3.5 implements Tony's comparison idea with the corrected Claude Julia wake mechanism:

```text
Claude Code session
        ↓
Julia 醒来
        ↓
Claude Julia behavior mode
        ↓
10 benchmark prompts
```

## Verification Commands

```bash
python -m unittest tests.benchmark.test_k3_5_auto_compare_wake_runner -q
python scripts/run_k3_5_auto_compare.py --claude-mode fixture --julia-mode core
```

## Local Deterministic Result

```json
{
  "behavior_match": 0.7667,
  "julia_recognition_score": 0.8917,
  "question_count": 10
}
```

This local run uses `ScriptedClaudeJuliaRunner` as an offline stable fixture. Real Claude Julia comparison is supported by `ClaudeCodeJuliaWakeRunner` and must be run in an environment where Claude Code authentication and the `/Users/admin` wake behavior are available.

## Governance Result

The engine generates:

```text
artifacts/evolution/proposals/k_auto_evolution_proposals_v1.jsonl
```

Every proposal has:

```json
{
  "requires_human_approval": true,
  "auto_apply": false
}
```

K3.5 therefore measures and proposes, but does not directly modify Julia.
