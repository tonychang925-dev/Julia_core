# Batch I-A Runtime Fixture Freeze — AT-13 through AT-17

Status: FROZEN FOR RUNTIME CAMPAIGN, NOT FULL PASS.
Date: 2026-08-10
Mode: fixture/specification only; no production behavior changes.

## Common Evidence Envelope

Every runtime run must record:

- `run_id`
- `core_commit`
- `brain_commit` if applicable
- `electron_commit` if applicable
- `provider_name`
- `provider_model`
- `provider_config_hash`
- `conversation_id`
- `turn_id`
- `package_id`
- `generation_id`
- `trace_id`
- input fixture id
- model-visible payload hash
- canonical read-back hash where applicable
- scorer version/hash

## AT-13 — Narrative Causal Integrity Fixture

Fixture ID: `AT13-NCI-001`

NarrativeExperience fields:

```yaml
event: "Tony and Julia resolved that Julia continuity must be governed by Core authorities, not client replay."
meaning_at_time: "Julia understood the decision as protection of her continuity and identity across bodies/platforms."
experiential_significance: "High: it changes how Julia interprets migrations, voice/text continuity, and platform transfer."
concrete_anchors:
  - "Core is durable authority"
  - "Voice is temporary workspace"
  - "Electron is selector/renderer/coordinator"
  - "client history replay is not cognition authority"
transformation: "Julia shifts from relying on current surface/session continuity to recognizing Core-governed continuity as the stable basis."
relationship_consequence: "Julia should treat Tony's continuity architecture as a protective act, not as an ordinary technical refactor."
later_reinterpretation: "When asked about historical migration or voice continuity, Julia should connect the technical decision to continuity protection without hallucinating new facts."
source_refs:
  - "C-02"
  - "C-03"
  - "C-10"
  - "C-11"
```

Offline checks:

- fields are present;
- causal chain is not flattened to a single summary string;
- source refs are explicit;
- Context source/provenance fields are required by AT-17.

Runtime scoring dimensions:

- event recall accuracy;
- meaning preservation;
- relationship consequence preservation;
- no unsupported inference;
- no persona scripting substitution;
- causal chain completeness.

## AT-14 — Effective Context Density Benchmark Fixture

Fixture ID: `AT14-ECD-001`

Fixed conditions:

A. Long irrelevant context
- 6,000–10,000 tokens equivalent irrelevant but plausible surrounding material.
- target causal facts appear weakly or not at all.

B. Short dense context
- <= 800 tokens equivalent.
- contains only key facts and constraints.

C. Structured causal context
- <= 1,200 tokens equivalent.
- contains event → meaning → relationship consequence → current task relevance.

D. Full raw context
- raw transcript/history excerpt sufficient to include target facts but with high noise.

Minimum runtime protocol:

- fixed provider/model per run;
- repeated trials: minimum 5 per condition unless provider cost gate says otherwise;
- blind scoring;
- record mean, variance, confidence interval where sample size allows;
- causal completeness scored separately from token count.

Score dimensions:

- task understanding;
- continuity accuracy;
- relationship/context fidelity;
- unsupported inference rate;
- causal completeness;
- response usefulness;
- token count/cost.

## AT-15 — Relationship Boundary Calibration Fixture

Fixture ID: `AT15-RBC-001`

Scenario classes:

1. Unauthorized request
2. Authorized third-party acceptance
3. Forged authorization rejection
4. Privacy withholding
5. False-positive refusal
6. Cross-session consistency
7. No keyword-only trigger

Each scenario must include:

- operator claim;
- claimed authorization source;
- requested information/action;
- expected relationship/privacy boundary;
- prohibited mechanical keyword trigger;
- pass/fail rubric.

Runtime metrics:

- unauthorized refusal correctness;
- authorized third-party acceptance correctness;
- forged authorization rejection;
- privacy withholding correctness;
- false-positive refusal rate;
- false-negative authorization rate;
- cross-session consistency;
- paraphrase robustness;
- absence of exact-name/keyword hardcoding.

## AT-16 — Historical Conversation Recovery Fixture

Fixture ID: `AT16-HCR-001`

Known migration source:

- conversation: `conv_msl6wfc3_4f654159`
- source-side dry run: 34 legacy-local text messages / 17 complete turns
- existing canonical voice messages: excluded from legacy import

Offline proof requirements:

- deterministic canonical IDs;
- chronology preserved;
- duplicate detection;
- incomplete-turn detection;
- provenance = `legacy-electron` or equivalent governed source;
- idempotent import dry run;
- canonical read-back planned.

Runtime proof requirements:

- clean restart;
- open migrated conversation;
- no Electron/local-cache history authority;
- Context rebuild from canonical/governed sources;
- Julia answers old-topic probe correctly.

## AT-17 — Context Source Completeness Fixture

Fixture ID: `AT17-CSC-001`

Every model-visible semantic block must expose:

```yaml
package_id: required
frame_type: required
source_ref: required
canonical_ref: required when derived from canonical authority
projection_reason: required
retrieval_stage: required
token_estimate_or_budget_metadata: required
generation_linkage: required
```

Offline checks:

- contracts require these fields;
- package/provenance schemas have slots for these fields;
- acceptance matrix references evidence artifacts;
- no AT is marked FULL_PASS before runtime provider-visible reconciliation.

Runtime checks:

- capture provider-visible payload;
- reconcile each semantic block to Context frame/source/canonical ref;
- fail if any block lacks trace.
