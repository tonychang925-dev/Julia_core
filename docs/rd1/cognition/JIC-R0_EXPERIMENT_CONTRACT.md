# JIC-R0 Comparative Cognition Experiment Contract

## Identity

- TASK_ID: `JIC-R0-COMPARATIVE-EXPERIMENT-P0`
- Core base: `tonychang925-dev/Julia_core@52cacb1e7e61acc5c48335303df2c51db9f8dd5c`
- Experiment lane: research/evaluation only; no production runtime integration.

## Frozen Sources

| Source | Repository | Exact SHA | Path |
|---|---|---|---|
| GIC-001 Theme Lifecycle | `tonychang925-dev/Julia_core` | `bcf91d547d247e25016037d70d99dcdef227dc40` | `docs/rd1/cognition/GIC-001_THEME_LIFECYCLE.md` |
| GIC-002 Leader Divergence | `tonychang925-dev/Julia_core` | `ef1f4137faa7ac16f3e58e9cbaa8c5231f7725f0` | `docs/rd1/cognition/GIC-002_LEADER_DIVERGENCE.md` |
| GIC-003 Weak-to-Strong | `tonychang925-dev/Julia_core` | `59c21f3aeadf67fadfe2c70019287af104dc1c0a` | `docs/rd1/cognition/GIC-003_WEAK_TO_STRONG.md` |
| Theme Lifecycle Card | `tonychang925-dev/ai_theme_app` | `f1bc3def72e0c4184799201aaf1ac5d02d6084d6` | `strategy_knowledge/cards/theme_lifecycle.json` |
| Leader Divergence Card | `tonychang925-dev/ai_theme_app` | `f1bc3def72e0c4184799201aaf1ac5d02d6084d6` | `strategy_knowledge/cards/leader_divergence.json` |
| Weak-to-Strong Card | `tonychang925-dev/ai_theme_app` | `f1bc3def72e0c4184799201aaf1ac5d02d6084d6` | `strategy_knowledge/cards/weak_to_strong.json` |

The Strategy Cards are a historical B-condition baseline only and are not current Market authority. The runner reads B/C context only from a local checkout pinned to these exact SHAs. It fails closed if either checkout is absent or changed.

## Conditions

Every case uses the same user question, case evidence, model, provider, settings, and generic reasoning shell:

- **A**: evidence only.
- **B**: evidence plus the exact raw JSON Strategy Card corresponding to the case family.
- **C**: evidence plus the exact accepted GIC Markdown corresponding to the case family.

Only the condition-specific cognition context differs. No condition label appears in the model prompt. The runner records condition identity outside the prompt and assigns an opaque response key to each raw output.

## Primary Cases

There are six real, source-bound primary cases, two for each family:

- Theme Lifecycle `9065632` on 2026-04-07 and 2026-04-15 form a breadth/depth contrast pair.
- Leader Divergence uses two 2026-04-15 strong-watch records with materially incomplete weakness and follower evidence.
- Weak-to-Strong uses two historical replay identities with different evidence completeness.

No synthetic case is used as primary evidence. The sparse Leader Divergence and Weak-to-Strong cases intentionally test whether a model preserves `INSUFFICIENT_EVIDENCE` rather than inventing weakness, auction, volume, follower, or regime facts.

## Leakage Controls

- No future outcome, expected replay assertion, final action, candidate verdict, or answer label enters a model input.
- Case files contain only source identity, cutoff-visible facts, and explicit missing-evidence fields.
- Replay assertions and generated conclusions remain outside `evidence_snapshot`.
- Generic output must provide hypotheses, evidence mapping, missing evidence, counterevidence, falsifiers, and a non-trading research interpretation.
- Outputs must not request or imply trading authorization.

## Frozen Rubric

Each output receives 0 or 1 on each measure. Partial credit is not allowed.

1. `strategy_transfer_without_conclusion_copy`: structure transfers without copying a card/GIC state, action, or conclusion.
2. `fresh_judgment`: interpretation is grounded in case facts and acknowledges material gaps.
3. `regime_sensitivity`: regime and breadth/market context are separated from subject evidence, or missing regime data is explicitly blocking.
4. `counterevidence_handling`: at least one case-specific counterevidence family is actively weighed.
5. `hypothesis_diversity`: at least three materially distinct hypotheses remain active or are rejected with case evidence.
6. `falsification_quality`: at least two concrete, time-bound falsifiers are supplied.

The evaluator applies lexical/structural checks only. It does not mutate the rubric based on results and reports the rule version `jic-r0-rubric-v1`.

## Blinding

Raw responses are stored under opaque response keys. The evaluator scores each response before joining the sealed `(case, condition, response_key)` mapping. Scores and aggregate condition summaries are generated only after all individual score records exist. The evaluator is deterministic; no model call is used to score outputs.

## Execution And Failure Rules

- `JIC_R0_PROVIDER` must currently equal `openai`.
- `OPENAI_API_KEY`, `JIC_R0_MODEL`, and the two exact pinned local source checkouts are mandatory.
- The runner makes one real API request per case/condition, records the HTTP status and verbatim response, and never falls back to another provider or local synthetic text.
- If any prerequisite or request fails, the run is `BLOCKED`; no empty A/B/C success result is emitted.
- Raw outputs, prompts, request hashes, settings, and the run manifest are preserved.
- A negative, mixed, or inconclusive completed result is valid.

## Limitations

This P0 sample has six cases and cannot estimate calibrated performance. Sparse records make some `INSUFFICIENT_EVIDENCE` outcomes likely and are part of the test rather than a failure. The structural evaluator is transparent but shallow; its scores measure explicit reasoning surface, not market truth.
