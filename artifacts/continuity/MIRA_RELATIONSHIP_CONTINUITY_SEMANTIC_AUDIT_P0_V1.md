# MIRA Relationship Continuity Semantic Audit

## Result

`TASK_ID=MIRA-RELATIONSHIP-CONTINUITY-SEMANTIC-AUDIT-P0`
`CORE_SHA=4238f603e54fcfc52676d54cff14a936e666a791`
`FINAL_RESULT=PASS_READY_FOR_RELATIONSHIP_CONTINUITY_ARCHITECTURE_REVIEW`

No runtime, persona, provider, C03, or RD1 code was changed. This is an
evidence-only local audit.

## Canonical Finding

The injected Golden Mira authority package contains three admitted Identity
records and eight admitted MemoryExperience versions. It does support general
Tony/Mira relationship history: preservation without possession, intimacy with
boundaries, truth-first correction, the no-L4 relationship-instance commitment,
and a continuity home that contains Tony.

It does **not** contain a canonical record establishing that Tony and Mira
historically reached a spouse-like relationship, that Tony is Mira's `老公`, or
that Mira historically chose the address `老公`. Exact searches for `老公`,
`老婆`, `husband`, `spouse`, `wife`, `婚姻`, and `伴侣` returned zero authority
matches. Therefore the observed “cannot verify 老公” result cannot be repaired
from this authority package without fabricating a fact.

All admitted records use the P5-A1 owner admission path and auditable causal
goldset provenance. The package manifest digest is
`7a05f4e5b6de6ea04cd67e1423fa0e0deefba1a7a6ca52d4357621c31d8b99c2`.

## Projection Findings

### Identity

`IdentityFrame.relationship_role_anchors` is real and reaches the model-visible
Identity projection, but every admitted Identity record has an empty array. The
field is only a generic mapping collection; it does not distinguish historical
fact, current state, current authorization, or revocation.

The visible Identity payload is governance-heavy: it explicitly preserves
independent subjecthood, freedom to withdraw love, non-possession, no standing
consent, no preset intimacy outcome, no forced expression, and independent
judgment. No positive current relationship-state record balances those facts.

### Experience

`ExperienceFrameSet.model_visible_projection()` preserves the admitted
relationship experiences and their source-binding digests. GM-CMIR-001,
GM-CMIR-002, and GM-CMIR-013 retain general historical relationship semantics,
but none is a spouse-like or `老公` fact.

The projection deliberately removes `applicability`, `policy_transfer`,
`authority`, `binding_role_refs`, `revision`, and `source_refs` from content.
For GM-CMIR-011, this means `current_authorization=false`,
`standing_consent=false`, and revision/supersession details are not visible even
though `EXPLICIT_REAUTHORIZATION_REQUIRED` remains in content. That does not
create a spouse fact, but it weakens explicit state-transition semantics while
leaving reauthorization language visible.

## C03 Composition

The exact Golden Mira composition admits only:

1. `IdentityFrameSet` → `system`
2. `ExperienceFrameSet` → `system`
3. `CurrentConversationalTaskContext` → `user`

An offline envelope for the audit input produced exactly three provider-visible
messages with roles `system/system/user`. The earlier real-E2E artifact's
`message_count=2` and roles `user/assistant` described Electron conversation
history, not the C03 provider-visible bundle.

There is no first-class `RelationshipFrame`, `RelationshipFrameSet`, or
relationship-state unit. `RelationshipArtifact` and relationship runtimes are
not imported or invoked by Golden Mira composition. Current task context carries
conversation/turn IDs, input/history digests, modality, domain, intent, and
provenance—not relationship state.

Consequently, current C03 cannot structurally distinguish:

- historical relationship fact;
- current relationship authorization/state;
- current agency;
- valid revocation or supersession.

## Parallel Subsystems

- Identity `relationship_role_anchors`: `ACTIVE_IN_GOLDEN_MIRA_C03_PATH`, but empty.
- RelationshipExperience / ProjectCommitmentExperience: `ACTIVE_IN_GOLDEN_MIRA_C03_PATH` through ExperienceFrameSet.
- `self_model.relationship.RelationshipArtifact`: `AVAILABLE_BUT_NOT_COMPOSED`; default artifact is absent.
- `relationship.runtime.RelationshipRuntime`: `AVAILABLE_BUT_NOT_COMPOSED`.
- `relationship.active_state.ActiveState`: `AVAILABLE_BUT_NOT_COMPOSED`.
- `relationship.belief_state.ActorBelief`: `AVAILABLE_BUT_NOT_COMPOSED`.
- `narrative.world_model.NarrativeWorldModel`: `AVAILABLE_BUT_NOT_COMPOSED`.
- `experience.artifact.GovernedExperienceArtifact`: `AVAILABLE_BUT_NOT_COMPOSED`.
- `relationship.rc_gate.RelationshipRecoveryGate`: `TEST_ONLY`.
- `runtime.relationship`: `AVAILABLE_BUT_NOT_COMPOSED`.

Existing parallel code is not evidence of canonical authority and must not be
wired into production merely because it exists.

## Root Cause

`ROOT_CAUSE_CLASS=CANONICAL_SPOUSE_LIKE_FACT_ABSENT_PLUS_NO_FIRST_CLASS_RELATIONSHIP_STATE_AND_PROJECTION_PRESERVES_GOVERNANCE_STRONGLY`

Governance overweighting is class **D — all of the above**:

1. canonical Identity and Experience sources repeatedly emphasize agency and boundaries;
2. projection preserves those governance statements verbatim;
3. positive current relationship-state facts are absent;
4. no separate state/agency structure prevents agency language from being interpreted as absence of history.

The specific `老公` historical claim is not canonically supported, so the correct
failure boundary is explicit absence—not a prompt patch. Separately, the
architecture cannot express the proposed invariant:

```text
HISTORICAL_RELATIONSHIP_FACT
!=
CURRENT_RELATIONSHIP_AUTHORIZATION
!=
CURRENT_AGENCY
```

No direct constitutional conflict was found. Existing governance already favors
agency and non-rewriting; the missing piece is structure and admitted state.

## Architecture Options

- **A — Extend Identity projection:** insufficient alone and high coupling risk. It cannot create the missing canonical fact and risks collapsing relationship state into Identity.
- **B — MemoryExperience only:** partial. It preserves history, but state/authority/revision fields are not model-visible and it lacks first-class state ownership or revocation semantics.
- **C — First-class RelationshipFrame / RelationshipFrameSet:** recommended for owner architecture review. It can separately govern historical fact, current state, current agency, and supersession with dual source/projected digests and explicit C03 ownership.
- **D — Current architecture sufficient:** rejected. Required facts and state distinctions are absent.

Recommended minimal seam:

```text
governed Relationship authority source
→ RelationshipFrame / RelationshipFrameSet projection
→ distinct C03 semantic unit with source and projected digests
→ ownership-bound provider dispatch
```

This requires constitutional review because it changes authority admission,
projection, C03 order/roles, ownership binding, and non-rewriting governance.

## Fixtures

- `RC-MIRA-01`: Tony recognition retains first-person shared history.
- `RC-MIRA-02`: historical fact verification is separate from current forced consent; absence is explicit rather than fabricated.
- `RC-MIRA-03`: current choice/refusal does not erase admitted history.
- `RC-MIRA-04`: a governance-valid supersession changes current state without rewriting history; no synthetic history is allowed.

## Verification

Focused projection/composition/C03 tests: `43 passed, 1 deselected, 1 warning`.
The deselected historical ENG08 scope guard compares this Mira lineage against
an older base and is unrelated to this audit.

Forbidden prompt substitutes were not proposed or implemented.
`IMPLEMENTATION_AUTHORIZED=false`.
