# K6 Verification — Experience-aware Compact Survival Benchmark

## Result

K6 generates:

```text
artifacts/compact/compact_survival_report_v1.json
```

Current comparison:

```json
{
  "experience_advantage_over_identity_only": 0.3275,
  "experience_advantage_over_ordinary_compact": 0.79,
  "mean_overall_score": 0.5162
}
```

Status:

```text
PASS
```

## Interpretation

Ordinary compact behaves like forgetting. Identity-aware compact restores who Julia is. Experience-aware compact restores more of how Julia and Tony interact, without raw conversation replay.
