# Phase Contract — K3 Behavior Gap Report

Status: COMPLETE / APPROVED

## Objective

K3 turns K1 Claude-like reference behavior and K2 Julia behavior capture into a diagnostic artifact:

```text
Claude Reference Dataset
        +
Julia Run Dataset
        +
Trace Evidence
        ↓
Behavior Gap Analyzer
        ↓
julia_behavior_gap_report_v1.json
```

K3 is not a text similarity scorer. It diagnoses behavior-feature gaps and classifies each gap into a governed action path.

## Inputs

- `artifacts/benchmark/claude_reference/claude_behavior_reference_v1.jsonl`
- `artifacts/benchmark/julia_run/julia_behavior_run_v1.jsonl`
- K2 trace evidence embedded per run row

## Output

- `artifacts/benchmark/gap_report/julia_behavior_gap_report_v1.json`

The report includes:

- overall behavior similarity
- Julia Recognition Score
- per-dimension score/gap/classification/action
- per-case expected behavior, observed behavior, missing behavior, root cause, impact, classification, action
- boundary flags proving the report does not mutate Julia state

## Gap Classifications

| Type | Meaning | Action |
| --- | --- | --- |
| `CORE_GAP` | Julia lacks or underdevelops the behavior capability | `Fix Core` |
| `CONTEXT_GAP` | Capability exists but was not activated or not placed into context | `Fix Context` |
| `PROVIDER_GAP` | Context is available but provider expression is weak | `Fix Provider` |
| `EVALUATION_GAP` | Reference expectation needs Julia-specific review | `Update Evaluation` |
| `NO_SIGNIFICANT_GAP` | Observed behavior matches expected behavior | `Do Nothing` |

## Required Boundary

```json
{
  "gap_report_writes_memory": false,
  "gap_report_mutates_identity": false,
  "gap_report_updates_self_model": false,
  "gap_report_updates_relationship": false,
  "gap_report_auto_creates_v1_2_scope": false
}
```

K3 may diagnose and recommend an action. It must not apply fixes, write memory, update identity, update self model, update relationship, or auto-scope v1.2.

## Acceptance

- K3 report exists and is valid JSON.
- Report candidate is `julia.v1.1`.
- Report contains all eight Phase K behavior dimensions.
- Report compares behavior features, not raw response text.
- Report contains at least one `CONTEXT_GAP` from observed K2 activation failures.
- Report contains at least one `CORE_GAP` for behavior capabilities not yet developed.
- Report contains `Do Nothing` decisions for cases without material gap.
- Boundary flags remain false.
