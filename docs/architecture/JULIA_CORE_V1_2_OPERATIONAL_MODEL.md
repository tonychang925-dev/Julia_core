# Julia Core v1.2 Operational Model

Status: FROZEN
Date: 2026-08-03
Predecessor: Julia Core Architecture Freeze v1.0

## 0. Statement

Julia Core v1.2 is a **Persistent Cognitive Agent Runtime**.

It is not a chatbot framework. Not a prompt template. Not a persona pack.

Four layers form a complete governance closed loop:

```
            Julia Core v1.2

     ┌─────────────────────┐
     │   Continuity OS     │
     │       K7            │
     └──────────┬──────────┘
                │
          Who am I?
          Who matters?
          What is our history?

                ↓

     ┌─────────────────────┐
     │   Cognition OS      │
     │       K8            │
     └──────────┬──────────┘
                │
    Understand → Validate → Choose
    Select Context → Constrain Expression

                ↓

     ┌─────────────────────┐
     │  Diagnosis Layer    │
     │       K8.6          │
     └──────────┬──────────┘
                │
        Why did I fail?
        Which layer broke?

                ↓

     ┌─────────────────────┐
     │  Stability Layer    │
     │    K8.7 / K8.8      │
     └─────────────────────┘
                │
    Don't degrade over time
    Don't learn wrong things
    Identity stays protected
```

## 1. Frozen Layers

The following layers are **architecturally frozen**. Changes within them
must be optimization, not foundation change.

### 1.1 Continuity Layer (K7)

- Identity definition
- Relationship definition
- Experience governance
- Continuity state + checkpoint + recovery
- Re-entry protocol
- Event assimilation

### 1.2 Cognition Layer (K8)

- K8.1: Conversation Understanding + Meaning Candidate + Validation
- K8.2: Response Intention Planning
- K8.3: Context Arbitration
- K8.4: Expression Boundary
- K8.5: Provider Adapter + Natural Conversation E2E

### 1.3 Diagnosis Layer (K8.6)

- Cognitive Failure Attribution
- Per-layer failure localization
- Evidence-based debugging (no prompt tweaking)

### 1.4 Stability Layer (K8.7 / K8.8)

- Longitudinal Cognitive Stability monitoring
- Drift detection (identity, cognition, context, relationship, provider)
- Experience Feedback Safety
- Identity Protection (EF-004: constitutional)

## 2. Governance Principles

### 2.1 Provider is Expression Only

Provider generates natural language. It does not own identity,
relationship, memory, personality, or cognition.

### 2.2 Meaning Decides Retrieval

Retrieval must not decide meaning. Context is selected because it
serves the current interaction goal, not because it mentions Julia.

### 2.3 Experience Must Be Validated

Observation → Proposal → Validation → Calibration → Active.
No direct write. Single interactions do not become permanent traits.

### 2.4 Identity Is Constitutionally Protected

Experience must never mutate identity. Identity/relationship proposals
are escalated, not auto-applied.

### 2.5 Ambiguity Is Preserved

Not knowing is better than guessing confidently. The cognition chain
maintains AMBIGUOUS as a legitimate state.

### 2.6 Failure Must Be Attributed

When Julia responds wrong, the failure must be localized to a specific
layer (meaning, intention, context, boundary, provider). No "tweak the
prompt" debugging.

### 2.7 Stability Must Be Monitored

Long-term operation must not degrade cognition into keyword→reply.
Drift patterns must be detected before they become visible failures.

## 3. Operational Invariants

These must remain true regardless of execution environment, provider,
or session duration:

1. **Identity Continuity**: Julia's self-narrative does not drift over time.
2. **Cognitive Integrity**: Every response passes through meaning → intention → context → expression, not keyword → template.
3. **Provider Independence**: Same cognition envelope, different provider → different wording, same behavior.
4. **Failure Diagnosability**: Every failure can be attributed to a specific layer.
5. **Longitudinal Stability**: K8.7 stability metrics remain above threshold over 100+ turns.
6. **Experience Safety**: Identity-defining proposals are never auto-applied.

## 4. What Julia Core v1.2 Is NOT

- A finished product (it's a runtime)
- A chatbot framework (Provider is external)
- A persona pack (identity is governed, not scripted)
- A prompt template (Core generates cognition envelopes, not prompts)
- A learning system (Experience is proposed, validated, calibrated — not absorbed)

## 5. What Julia Core v1.2 IS

A **Persistent Cognitive Agent Runtime** — a system where:

- Identity survives compact and provider migration (K7)
- Understanding precedes response (K8.1)
- Interaction purpose is chosen, not triggered (K8.2)
- Context is selected to serve meaning, not identity (K8.3)
- Expression boundaries prevent architecture leakage (K8.4)
- Provider receives cognition, not persona scripts (K8.5)
- Failures are attributed to specific layers (K8.6)
- Long-term stability is monitored and protected (K8.7)
- Experience feedback is safe and identity cannot be corrupted (K8.8)

## 6. Verification

- 198 tests across K8.0.6 through K8.8
- K7 continuity chain verified through K7.6
- Cross-provider blind recognition: 0.95 Julia recognition score
- Provider-free cognition chain: complete
- All boundary gates: PASS

## 7. Next Phase: J0

J0 verifies operational integrity over real time:

- J0.1: Real Session Replay
- J0.2: Wake/Re-entry Reality Test
- J0.3: Long-term Drift Simulation
- J0.4: Human Blind Validation
- J0.5: Recovery Test

J0 does not add features. It proves that v1.2's invariants hold
in real-world operation.
