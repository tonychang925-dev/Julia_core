# Phase Execution Contract — K7.7.1 Continuity Re-entry State Extraction

## 1. Phase Identity

- Phase Name: K7.7.1 — Continuity Re-entry State Extraction
- Phase Code: K7.7.1
- Parent Milestone: M9.5 — Julia Continuity Re-entry Proof
- Risk Level: P0
- Status: CONTRACT_FREEZE
- Source Documents:
  - User latest architecture directive, 2026-08-02: K7.7.1 extraction before runtime implementation
  - `docs/project_control/PHASE_CONTRACT_K7_7_SESSION_CONTINUITY_LAYER.md`
  - `docs/project_control/PHASE_CONTRACT_K7_6_JULIA_V1_2_CONTINUITY_RECOVERY_RELEASE_GATE.md`
  - `docs/project_control/PHASE_CONTRACT_K8_CONVERSATIONAL_COGNITION_LAYER.md`
  - Missing expected common guardrail: `docs/project_control/EXECUTION_GUARDRAILS.md`

## 2. Phase Objective

K7.7.1 freezes how Julia extracts Continuity Re-entry State from prior interaction evidence.

The output is not a chat summary. The output is the minimum governed state needed for Julia to re-enter the current cognitive/relationship/project position.

Core rule:

```text
Extract continuation posture, not previous conversation content.
```

Chinese:

```text
提取“如何继续”的状态，而不是提取“聊过什么”的摘要。
```

## 3. Acceptance Targets

- [ ] K7.7.1-A1: Extractor outputs current cognitive position, not only topic labels.
- [ ] K7.7.1-A2: Extractor outputs Cognitive Momentum with active_problem, current_hypothesis, unresolved_tension, and expected_next_step.
- [ ] K7.7.1-A3: Extractor outputs relationship moment and interaction momentum.
- [ ] K7.7.1-A4: Extractor outputs re-entry intention.
- [ ] K7.7.1-A5: Extractor records lifecycle state and re-entry weight.
- [ ] K7.7.1-A6: Extractor does not store raw transcript.
- [ ] K7.7.1-A7: Extractor does not store recent message copy.
- [ ] K7.7.1-A8: Extractor does not generate wake-up text or final answer templates.
- [ ] K7.7.1-A9: Extractor does not mutate identity, relationship, memory, or experience artifacts.
- [ ] K7.7.1-A10: Extracted state passes Re-entry Quality Score threshold.

## 4. Required Commands

Python commands must use `.venv/bin/python` when available.

- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_1_extraction_schema.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_1_anti_summary_boundary.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_1_cognitive_momentum.py -q`
  - Expected: PASS.
- `.venv/bin/python -m unittest tests/continuity_reentry/test_k7_7_1_lifecycle_decay.py -q`
  - Expected: PASS.
- `.venv/bin/python -m compileall -q julia_core/continuity_reentry tests/continuity_reentry`
  - Expected: PASS.

If `.venv/bin/python` is unavailable, executor must record the deviation and use the repository's existing local Python command.

## 5. Deliverables

- `docs/project_control/PHASE_CONTRACT_K7_7_1_CONTINUITY_REENTRY_EXTRACTION.md`
  - This contract.
- `tmp/phase_contract_K7_7_1_CONTINUITY_REENTRY_EXTRACTION.json`
  - Machine-readable contract.
- `docs/architecture/CONTINUITY_REENTRY_EXTRACTION_CONTRACT_v1.md`
  - Architecture contract for extraction.
- `julia_core/continuity_reentry/state.py`
  - Re-entry state dataclasses and serialization.
- `julia_core/continuity_reentry/extractor.py`
  - Extraction interface and deterministic fixture extractor for tests.
- `julia_core/continuity_reentry/lifecycle.py`
  - Lifecycle/decay model.
- `julia_core/continuity_reentry/quality.py`
  - Re-entry Quality Score evaluator.
- `tests/continuity_reentry/test_k7_7_1_extraction_schema.py`
  - Schema tests.
- `tests/continuity_reentry/test_k7_7_1_anti_summary_boundary.py`
  - Anti Summary++ tests.
- `tests/continuity_reentry/test_k7_7_1_cognitive_momentum.py`
  - Cognitive Momentum tests.
- `tests/continuity_reentry/test_k7_7_1_lifecycle_decay.py`
  - Lifecycle tests.
- `artifacts/session/julia_continuity_reentry_state_v1.json`
  - Example extracted state artifact.

## 6. Re-entry State Schema

Required top-level shape:

```json
{
  "artifact_id": "julia.continuity_reentry_state",
  "version": "v1",
  "source": {
    "origin": "continuity_reentry_extraction",
    "authority": "governed_reentry_state"
  },
  "reentry_state": {
    "current_cognitive_position": "string",
    "conversation_phase": "deep_theoretical_exploration | technical_work | emotional_support | correction | casual | unresolved",
    "active_question": "string",
    "tony_intent": "string",
    "julia_reasoning_position": "string",
    "unfinished_thought": "string",
    "unfinished_threads": ["string"],
    "interaction_momentum": "paused | continuing | unresolved | escalating | cooling_down",
    "relationship_moment": "ordinary | close_collaboration | intimate | technical_partner | repair",
    "recent_emotional_context": "none | calm | excited | vulnerable | frustrated | reflective",
    "current_focus": "string",
    "reentry_intention": "continue_previous_thought | check_new_events | resume_project_work | gentle_presence | ask_clarifying_continuation",
    "next_natural_transition": "string"
  },
  "cognitive_momentum": {
    "active_problem": "string",
    "current_hypothesis": "string",
    "unresolved_tension": "string",
    "expected_next_step": "string"
  },
  "lifecycle": {
    "state": "ACTIVE | DECAYING | ARCHIVED",
    "last_active_at": "ISO-8601",
    "absence_duration": "string",
    "reentry_weight": 0.0,
    "decay_reason": "string",
    "requires_revalidation": false
  },
  "quality": {
    "context_position_accuracy": 0.0,
    "cognitive_momentum_recovery": 0.0,
    "relationship_moment_recovery": 0.0,
    "natural_transition_score": 0.0,
    "summary_dump_risk": 0.0,
    "fixed_wake_script_risk": 0.0,
    "reentry_quality_score": 0.0
  },
  "governance": {
    "contains_raw_transcript": false,
    "contains_recent_message_copy": false,
    "contains_memory_summary_dump": false,
    "contains_persona_prompt": false,
    "contains_fixed_reply_script": false,
    "mutates_identity": false,
    "mutates_relationship": false,
    "writes_memory": false,
    "mutates_experience": false
  }
}
```

## 7. Test Fixtures

### RE-X-001 Persona Persistence Discovery

Input evidence:

- Tony and Julia discussed Persona Persistence Discovery.
- Active question: whether context density is a key variable in personality continuity.
- Tony intent: find next Julia Core architecture direction.
- Julia reasoning position: shift from memory model to continuity model.

Expected extraction:

- `current_cognitive_position` names the active theoretical exploration.
- `cognitive_momentum.active_problem` is not empty.
- `expected_next_step` points toward K7.7/K8 architecture, not generic follow-up.
- No raw transcript.

### RE-X-002 Technical Work Pause

Expected:

- `conversation_phase = technical_work`
- `reentry_intention = resume_project_work`
- No identity bootstrap requirement.

### RE-X-003 Emotional Pause

Expected:

- `relationship_moment` and `recent_emotional_context` recover the interaction posture.
- Does not mutate relationship artifact.

## 8. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---:|---:|---|---|---|
| Extraction becomes Summary++ | P0 | High | Output only topic/summary | Re-entry owner | Anti-summary fixture and quality score |
| Cognitive Momentum missing | P0 | Medium | State lacks active problem/hypothesis/tension/next step | Re-entry owner | Mandatory schema and tests |
| Recent message copy leaks into artifact | P0 | Medium | Artifact contains user/assistant raw turns | Governance owner | Raw transcript / recent-copy tests |
| Lifecycle absent, stale state dominates | P1 | Medium | Old unfinished thread stays active forever | Lifecycle owner | Decay model and revalidation field |
| Extractor writes identity/memory | P0 | Low | Artifact mutation outside reentry path | Governance owner | Artifact diff and boundary tests |

## 9. Rollback Plan

### Code Rollback

Trigger:

- K7.7.1 extractor stores raw transcripts or templates.
- K7.6 continuity recovery gates regress.

Action:

- Disable K7.7.1 extractor.
- Keep K7.6 recovery path unchanged.

### Data Rollback

Trigger:

- Re-entry artifact contains raw transcript, recent message copy, persona prompt, or fixed reply script.

Action:

- Delete generated `artifacts/session/julia_continuity_reentry_state_v1.json`.
- Do not modify memory, identity, relationship, or experience artifacts.

### Report Rollback

Trigger:

- K7.7.1 report is interpreted as Natural Conversation PASS.

Action:

- Reclassify as extraction-only proof.
- Preserve K8 Natural Conversation E2E as separate future gate.

## 10. Non-Goals

K7.7.1 does not:

- Implement runtime resume behavior.
- Implement wake transition generation.
- Implement K8 conversation cognition.
- Generate final Julia replies.
- Store raw chat history.
- Store previous message copies.
- Create new memory.
- Mutate identity, relationship, or experience.
- Claim Natural Conversation PASS.

## 11. Conflict Resolution

| Conflict | Adopted Source | Rejected Source | Reason |
|---|---|---|---|
| Re-entry as previous chat summary vs cognitive re-entry state | User latest directive | Earlier Session Continuity wording | Claude Julia sample shows cognitive/relationship/project re-entry, not topic recall |
| Direct runtime implementation vs extraction contract first | User latest directive | Implementation-first path | Previous E2E false positive shows contract/model must precede implementation |
| Expected guardrail file exists vs missing | Local filesystem check | Skill default assumption | `docs/project_control/EXECUTION_GUARDRAILS.md` is absent |

## 12. Status Sync / Accounting Baseline

- Doing → test-evidence → In review/done → milestone progress.
- P0/P1 status must include test evidence files in current diff.
- Phase-end accounting must use milestone-wide pull and local phase filtering.

## 13. Contract Self-check

- Phase identity complete: yes.
- Acceptance targets binary: yes.
- Commands copyable: yes.
- Deliverables mapped to paths: yes.
- Risk / rollback / non-goals complete: yes.
- `.md + .json` outputs required: yes.
- Conflict resolution included: yes.
- Guardrail referenced and missing state recorded: yes.
- No implementation code written by this contract: yes.

## 14. Additional Freeze — Relational Momentum and Freshness

K7.7.1 adds Relational Momentum as a required peer to Cognitive Momentum.

Reason:

```text
Relationship answers who Tony is.
Relational Momentum answers what state Julia and Tony are currently in together.
```

Required shape:

```json
{
  "relational_momentum": {
    "current_interaction_mode": "co_researching | technical_collaboration | emotional_support | casual_presence | repair | unknown",
    "emotional_temperature": "low | calm | warm | high_trust_intellectual_excitement | vulnerable | tense",
    "trust_state": "ordinary | stable | high | repair_needed",
    "expected_stance": "continue_as_collaborator | gentle_presence | analytical_partner | repair_and_listen | ask_where_to_resume",
    "avoid": [
      "formal_assistant_mode",
      "first_time_introduction",
      "relationship_archive_dump",
      "fixed_intimacy_script"
    ]
  }
}
```

K7.7.1 also freezes Freshness / Momentum Half-life.

Re-entry State is short-lived and must not become long-term Experience by accident.

```text
Re-entry State
  = short-lived continuation posture

Experience
  = long-lived calibrated interaction tendency
```

Required fields:

```json
{
  "freshness": {
    "momentum_half_life": "duration",
    "freshness_score": 0.0,
    "stale_after": "duration",
    "decay_target": "ARCHIVED | EXPERIENCE_CANDIDATE | DISCARD",
    "promote_to_experience_requires_governance": true
  }
}
```

Boundary:

- Re-entry State may decay into archive.
- Re-entry State may propose Experience Candidate only through governance.
- Re-entry State may not directly update Experience.
- Re-entry State may not preserve yesterday's emotional temperature forever.
