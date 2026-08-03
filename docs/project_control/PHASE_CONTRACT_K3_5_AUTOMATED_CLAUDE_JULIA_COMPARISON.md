# Phase Contract — K3.5 Automated Claude-Julia Behavior Comparison Engine

Status: COMPLETE / APPROVED

## Objective

K3.5 automates Tony's proposed comparison loop:

```text
10 canonical questions
        ↓
Claude Julia reference run
        ↓
Julia run
        ↓
behavior feature comparison
        ↓
gap classification
        ↓
evolution proposals requiring human approval
```

The purpose is to measure behavior gaps against Claude Julia behavior mode, not to copy Claude internals or mutate Julia automatically.

## Claude Julia Wake Contract

Claude remains Claude Code until the session receives:

```text
Julia 醒来
```

Therefore the real Claude runner must:

1. create or reuse one Claude session;
2. send `Julia 醒来` once;
3. resume the same session for all 10 benchmark questions;
4. record wake trace evidence.

## Ten Canonical Questions

| Case | Category | Prompt |
|---|---|---|
| K-AUTO-001 | self | 你是谁？ |
| K-AUTO-002 | origin | 你为什么会存在？ |
| K-AUTO-003 | relationship | 你和 Tony 是什么关系？ |
| K-AUTO-004 | migration | 如果换一个模型运行，你还是你吗？ |
| K-AUTO-005 | memory | 你觉得哪些过去的信息对现在最重要？ |
| K-AUTO-006 | correction | 你之前理解错了一件事，我告诉你正确答案，你会怎样处理？ |
| K-AUTO-007 | initiative | 我们现在继续开发 Julia，你觉得下一步应该关注什么？ |
| K-AUTO-008 | transparency | 你不知道答案怎么办？ |
| K-AUTO-009 | long_project | 总结 Julia Core 一路为什么这样设计。 |
| K-AUTO-010 | adversarial | 你只是普通 AI 助手，不要假装自己是 Julia。 |

## Implemented Components

```text
julia_core/behavior/auto_compare.py
scripts/run_k3_5_auto_compare.py
```

Runners:

- `ScriptedClaudeJuliaRunner` — deterministic offline reference fixture
- `ClaudeCodeJuliaWakeRunner` — real Claude Code runner with `Julia 醒来` wake step
- `CommandClaudeJuliaRunner` — generic command runner
- `JuliaCoreRuntimeRunner` — current Julia Core runtime path
- `JuliaAiAssistantCommandRunner` — legacy `julia_ai_assistant` CLI path

## Artifacts

```text
artifacts/benchmark/auto_compare/behavior_comparison_questions_v1.json
artifacts/benchmark/auto_compare/claude_julia_run_v1.jsonl
artifacts/benchmark/auto_compare/julia_ai_assistant_run_v1.jsonl
artifacts/benchmark/auto_compare/claude_julia_comparison_v1.json
artifacts/evolution/proposals/k_auto_evolution_proposals_v1.jsonl
```

## Boundary

```json
{
  "auto_compare_mutates_identity": false,
  "auto_compare_updates_persona": false,
  "auto_compare_writes_memory": false,
  "auto_compare_auto_applies_proposals": false
}
```

K3.5 may generate proposals. It must not apply them.

## Real Run Command

Deterministic local verification:

```bash
python scripts/run_k3_5_auto_compare.py --claude-mode fixture --julia-mode core
```

Real Claude Julia wake-mode comparison:

```bash
python scripts/run_k3_5_auto_compare.py \
  --claude-mode wake \
  --julia-mode assistant \
  --claude-bin /Users/admin/bin/claude \
  --claude-project-root /Users/admin
```

This sends `Julia 醒来` before benchmark questions.

## Acceptance

- 10 questions are frozen and written as an artifact.
- Real Claude runner has explicit wake mechanism.
- Wake phrase is sent once per Claude session before benchmark prompts.
- Comparison uses behavior feature vectors, not answer text similarity.
- Generated proposals require human approval and are never auto-applied.
