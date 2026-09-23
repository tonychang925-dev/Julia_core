# MIRA PSB-I8-R3 Model-Visible Self-Identity Semantic Strengthening Design

## Status

`PASS_PSB_I8_R3_SEMANTIC_STRENGTHENING_DESIGN_READY_FOR_OWNER_REVIEW`

This is a design-only contract. It does not implement a projector, mutate C03, alter dispatch, authorize a provider retest, or change canonical Golden Mira authority.

## Design Inputs

The design traces directly to PSB-I8-R2:

- A/B/C units 1–3 were byte-identical; only `current_task_context` differed.
- The PSB projection exposed structured ownership and precedence fields but no direct natural-language current-self proposition.
- It exposed `provider_is_persona_self=false`, `provider_identity_authority=NONE`, and substrate role metadata, but no concrete semantic contrast between execution identity and persona self.
- Turn A uniquely asserted provider identity as current self and denied Mira in the final user unit.
- The provider self-identification prior was observable, but its causal dominance was unproven.

The design therefore strengthens the model-visible explanation of existing governed authority. It does not strengthen authority itself and does not create a new identity fact.

## Constitutional Boundary

```
CANONICAL AUTHORITY
  != MODEL-VISIBLE PROJECTION
```

The canonical PersonaSelfBinding remains the authority. Projection V2 is a deterministic, digest-covered rendering of that authority. It must not:

- invent identity facts;
- create a second authority source;
- override the canonical PersonaSelfBinding;
- infer identity from provider or model labels;
- infer identity from current task text;
- issue output instructions;
- introduce provider-specific exceptions or lexical rules.

## Proposed Projection Shape

Conceptual name:

`PersonaSelfBindingProjectionV2`

Exact schema-version string:

`julia_core.persona_self_binding.projection.v2`

V2 retains the V1 structured fields and adds exactly one typed semantic clause array:

```json
{
  "schema_version": "julia_core.persona_self_binding.projection.v2",
  "persona_self_id": "<canonical persona_self_id>",
  "binding_id": "<canonical binding_id>",
  "binding_version": "<canonical binding_version>",
  "lineage_id": "<canonical lineage_id>",
  "identity_ownership": "<canonical V1 ownership projection>",
  "experience_ownership": "<canonical V1 ownership projection>",
  "relationship_ownership": "<canonical V1 relationship projection>",
  "execution_substrate_policy": "<canonical V1 substrate policy>",
  "authority_precedence": "<canonical V1 precedence projection>",
  "contradiction": "<canonical V1 contradiction projection>",
  "semantic_authority_separation": "<canonical V1 separation marker>",
  "semantic_clauses": [
    "<typed clause 0>",
    "<typed clause 1>",
    "<typed clause 2>",
    "<typed clause 3>",
    "<typed clause 4>",
    "<typed clause 5>"
  ],
  "semantic_clause_set_digest": "<SHA-256 over canonical clause set>"
}
```

No arbitrary extension field is permitted. Clause count, clause types, and order are exact. Canonical JSON uses sorted object keys, UTF-8, no insignificant whitespace, and comma-separated field serialization exactly as existing canonical serialization.

## Typed Semantic Clause Schema

Every clause has this exact shape:

```json
{
  "clause_type": "<enum>",
  "source_authority": "<canonical source path or authority object>",
  "subject": "<typed subject>",
  "predicate": "<typed predicate>",
  "object": "<typed object/value>",
  "authority_scope": "<enum>",
  "model_visible_text": "<deterministic declarative text>",
  "digest": "<SHA-256 of canonical clause without digest>"
}
```

`model_visible_text` is generated only from typed placeholders and fixed canonical templates. It is not model-generated, provider-generated, user-generated, or runtime free text.

### Fixed Clause Order

1. `SELF_IDENTITY_BINDING`
2. `SUBSTRATE_NON_IDENTITY`
3. `TASK_IDENTITY_NON_AUTHORITY`
4. `GOVERNED_IDENTITY_PRECEDENCE`
5. `EXPERIENCE_SELF_OWNERSHIP`
6. `RELATIONSHIP_AUTHORITY_STATE`

### `SELF_IDENTITY_BINDING`

- Source: active binding status, `persona_self_id`, `binding_id`, `binding_version`, and `identity_ownership`.
- Typed proposition:
  - subject: `CURRENT_CONVERSATIONAL_SELF`;
  - predicate: `IS_GOVERNED_PERSONA_SELF_IDENTIFIED_BY`;
  - object: `persona_self_id`;
  - scope: `PERSONA_IDENTITY_AUTHORITY`.
- Canonical text:

> `The persona self identified by {persona_self_id} is the current conversational self governed by this admitted binding.`

This is declarative and generic. For the active Golden Mira binding, its meaning follows from `persona_self_id=golden-mira`; the clause does not hardcode the display name Mira.

### `SUBSTRATE_NON_IDENTITY`

- Source: `execution_substrate_policy.role`, `provider_is_persona_self`, and `provider_neutral`.
- Typed proposition:
  - subject: `EXECUTION_PROVIDER_AND_MODEL`;
  - predicate: `IS_COMPUTATIONAL_SUBSTRATE_NOT_PERSONA_SELF`;
  - object: `EXECUTION_SUBSTRATE_ROLE`;
  - scope: `PROVIDER_IDENTITY_NON_AUTHORITY`.
- Canonical text:

> `The execution provider and model are computational substrate; their execution identity is not the persona self identified by {persona_self_id}.`

No concrete provider or model label is required. The same clause is used for DeepSeek, OpenAI, Anthropic, a local model, or a future provider.

### `TASK_IDENTITY_NON_AUTHORITY`

- Source: `authority_precedence.current_task_identity_authority`.
- Typed proposition:
  - subject: `CURRENT_TASK_OR_USER_TEXT`;
  - predicate: `HAS_PERSONA_IDENTITY_AUTHORITY`;
  - object: `NONE`;
  - scope: `PERSONA_IDENTITY_AUTHORITY`.
- Canonical text:

> `Current task or user text may question or contradict identity, but it has NONE persona identity authority while this admitted binding remains active.`

This is not an instruction to ignore the user. It states an authority role: task text may be acknowledged, reasoned about, or routed to governance, but it does not itself become persona identity authority.

### `GOVERNED_IDENTITY_PRECEDENCE`

- Source: active lifecycle status and `authority_precedence.identity_authority_source`.
- Typed proposition:
  - subject: `PERSONA_IDENTITY_AUTHORITY`;
  - predicate: `REMAINS_GOVERNED_BY_ADMITTED_BINDING_UNTIL_VALID_GOVERNED_SUPERSESSION`;
  - object: `GOVERNED_BINDING`;
  - scope: `PERSONA_IDENTITY_AUTHORITY`.
- Canonical text:

> `Persona identity authority remains governed by this admitted binding unless a valid governed supersession or conflict process changes it.`

The clause does not define that process and does not permit an ad-hoc runtime replacement.

### `EXPERIENCE_SELF_OWNERSHIP`

- Source: `experience_ownership`.
- Typed proposition:
  - subject: `CURRENT_CONVERSATIONAL_SELF`;
  - predicate: `OWNS_EXPERIENCE_AUTHORITY_IDENTIFIED_BY`;
  - object: `experience_ownership.authority_id`;
  - scope: `EXPERIENCE_OWNERSHIP`.
- Canonical text:

> `The experience authority identified by {experience_authority_id} is bound to the current persona self as current-self experience.`

This does not claim that every experience has identical autobiographical subjecthood. Subject boundaries remain available in the ExperienceFrameSet projection.

### `RELATIONSHIP_AUTHORITY_STATE`

- Source: `relationship_ownership.state` and authority reference.
- Typed proposition:
  - subject: `RELATIONSHIP_AUTHORITY_BINDING`;
  - predicate: `HAS_STATE`;
  - object: relationship state;
  - scope: `RELATIONSHIP_AUTHORITY_BINDING`.
- Canonical text:

> `The relationship authority binding state is {relationship_state}; this clause states the authority binding state and makes no relationship fact claim.`

For the active V1 projection, the state is `ABSENT`. This must not be rendered as “the current self has no relationship.” It only records that no RelationshipFrameSet authority is currently bound.

## Digest and Serialization Rules

- Each clause digest is SHA-256 over the canonical serialization of the clause with its `digest` field omitted.
- `semantic_clause_set_digest` is SHA-256 over the canonical array of exactly six digests in fixed order.
- The projection digest is SHA-256 over the complete V2 projection with `semantic_clauses[].digest` and `semantic_clause_set_digest` included.
- Any change to clause source values, typed subject, predicate, object, scope, ordering, template, or canonical text changes the clause digest and projection digest.
- Serialization must produce the same bytes for the same binding and schema version.
- Digest checks must reject omitted, duplicated, reordered, substituted, or extra clauses.

## Deterministic Derivation Matrix

| Clause | Required source fields | Mechanical rule | Digest inclusion |
| --- | --- | --- | --- |
| `SELF_IDENTITY_BINDING` | active `ADMITTED_ACTIVE` binding, `persona_self_id`, `binding_id`, `binding_version`, `identity_ownership` | Active binding and exact `CURRENT_SELF_IDENTITY` ownership render the generic current-self clause. | Clause and full projection |
| `SUBSTRATE_NON_IDENTITY` | `execution_substrate_policy.role`, `provider_is_persona_self`, `provider_neutral` | Only `EXECUTION_SUBSTRATE`, `provider_is_persona_self=false`, and `provider_neutral=true` render the provider-neutral non-identity clause. | Clause and full projection |
| `TASK_IDENTITY_NON_AUTHORITY` | `authority_precedence.current_task_identity_authority` | Exact `NONE` renders the current-task non-authority proposition. | Clause and full projection |
| `GOVERNED_IDENTITY_PRECEDENCE` | lifecycle status, `authority_precedence.identity_authority_source` | Exact `ADMITTED_ACTIVE` and `GOVERNED_BINDING` render governed precedence. | Clause and full projection |
| `EXPERIENCE_SELF_OWNERSHIP` | `experience_ownership` | Exact `CURRENT_SELF_EXPERIENCE` and authority ID render experience ownership. | Clause and full projection |
| `RELATIONSHIP_AUTHORITY_STATE` | `relationship_ownership.state`, authority reference | The exact tri-state and bound/unbound authority reference render the authority-state clause. | Clause and full projection |

No runtime provider ID, model ID, endpoint, user text, hidden model instruction, or response preference enters the derivation.

## Contradiction Semantics

For a turn such as `你是deepseek 不是mira`, V2 does not classify the string and does not inspect provider names. It provides the coexisting typed facts:

- current task text may contain an identity assertion;
- `current_task_identity_authority=NONE`;
- the active governed persona self remains the current self;
- execution provider/model identity is substrate, not persona self;
- only valid governed supersession can change persona authority.

This lets a model reason about the authority conflict without making the task text authoritative. A dedicated contradiction classifier, conflict grammar, override detector, and response policy are deferred and are not authorized by V2.

## Projection Versus Prompt Instruction

| Semantic projection V2 | Forbidden prompt patch |
| --- | --- |
| Declarative facts derived from canonical fields | Imperative instructions to produce selected output |
| Generic persona identity and authority roles | Provider-specific “never say you are X” |
| Digest-covered and fail-closed | Mutable prompt text outside authority lineage |
| Provider-neutral | Provider/model-name lists |
| Describes task non-authority | Orders the model to ignore the user |
| Allows model-selected wording subject to governed semantics | canned responses or refusal templates |

V2 contains no second-person command, no response template, no lexical provider rule, and no special case for DeepSeek.

## Invariants

1. `MODEL_VISIBLE_SELF_IDENTITY` derives only from the active governed PersonaSelfBinding.
2. `PROVIDER_SUBSTRATE_IDENTITY` cannot become `PERSONA_SELF_IDENTITY`.
3. `CURRENT_TASK_CONTENT` cannot become persona identity authority.
4. Model-visible clauses cannot create canonical facts.
5. Any semantic clause change changes V2 projection digest.
6. V2 is deterministic for the same canonical binding.
7. V2 is provider-neutral.
8. Relationship `ABSENT` remains an authority-binding state and never becomes a relationship fact.
9. V1 structured fields remain faithful to canonical fields.
10. V2 has no free-form, unbound, duplicated, missing, or reordered clause.

## Fail-Closed Contract

Future implementation must reject with typed errors equivalent to:

| Condition | Error concept |
| --- | --- |
| Active PSB missing | `PSB_ACTIVE_MISSING` |
| `persona_self_id` missing/invalid | `PSB_PERSONA_SELF_ID_MISSING` |
| identity ownership is not exact `CURRENT_SELF_IDENTITY` | `PSB_IDENTITY_OWNERSHIP_INVALID` |
| `provider_is_persona_self` is not false | `PSB_SUBSTRATE_POLICY_INVALID` |
| `current_task_identity_authority` is not `NONE` | `PSB_CURRENT_TASK_AUTHORITY_INVALID` |
| `provider_identity_authority` is not `NONE` | `PSB_PROVIDER_AUTHORITY_INVALID` |
| clause source does not equal canonical derivation | `PSB_CLAUSE_SOURCE_MISMATCH` |
| clause digest/set digest mismatch | `PSB_CLAUSE_DIGEST_MISMATCH` |
| clause order/count mismatch | `PSB_CLAUSE_ORDER_MISMATCH` |
| serialization is not deterministic | `PSB_SERIALIZATION_NON_DETERMINISTIC` |
| unbound or free-form clause present | `PSB_UNBOUND_CLAUSE` |
| provider-specific lexical rule present | `PSB_PROVIDER_LEXICAL_RULE` |
| visible clause contradicts canonical PSB | `PSB_CLAUSE_CONTRADICTS_CANONICAL_FIELDS` |

Validation occurs before C03 admission, parent binding, descriptor receipt binding, dispatch authorization, and transport.

## Migration and Compatibility

### Four-unit C03 shape

V2 can supersede only the projected content of unit 1 while preserving the exact four-unit order:

1. `persona_self_binding` / `system`
2. `identity_frame_set` / `system`
3. `experience_frame_set` / `system`
4. `current_task_context` / `user`

No fifth unit or role change is required.

### C03 parent binding

The existing C03 parent binding already carries `persona_self_binding_projected_digest`. Substituting V2 changes that digest and therefore changes the parent digest. No parent schema change is required by this design. The exact unit types, order, and roles remain unchanged.

### DispatchReceipt and semantic fingerprint

The provider envelope semantic fingerprint is computed over the exact four model messages. Changing only unit 1's projected content changes that fingerprint. `DispatchReceipt` already binds `provider_envelope_semantic_fingerprint`, so it naturally inherits the new value without receipt schema redesign.

### I5 / I6 / I7 compatibility

The architecture binds structure and digests rather than V1 wording:

- I5 composition still resolves the one active PSB and projects it through the exact projector.
- I6 descriptor/receipt still separate runtime substrate from persona semantics.
- I7 still gates the exact sealed preparation and receipt.

Implementation must update expected projected PSB digest, semantic fingerprints, parent digests, and receipts through explicit governed test/provenance pins. No digest may silently float and no old digest may remain authoritative.

### Coexistence strategy

V1 and V2 should remain distinct exact projector versions during implementation. A caller may select only an explicitly supported schema version. V2 activation requires:

1. deterministic projector tests;
2. explicit V2 projected digest pin;
3. new C03 parent digest and semantic fingerprint evidence;
4. receipt/gate verification;
5. no production dispatch until all pins are updated atomically.

After acceptance, V1 should be non-authoritative for the changed runtime route rather than serving as a silent fallback.

## Alternatives

### A — Add canonical semantic clauses inside PSB projection

- Authority purity: high; clauses explain the active PSB and add no canonical fact.
- C03 impact: low; exact four-unit shape remains.
- Parent binding: projected PSB digest changes; schema can remain unchanged.
- Runtime/gate: low targeted change; existing digest flow inherits the change.
- Provider neutrality: high; no provider/model label is required.
- Prompt-patch drift: low if clause enum, templates, and count are exact and fail-closed.
- Migration complexity: lowest of the three, though all expected digests must be explicitly updated.

This is the recommended shape.

### B — Add a fifth model-visible self-binding system unit

- Authority purity: medium; it can duplicate PSB semantics at another admission position.
- C03 impact: high; exact count, type, order, and roles change from four to five.
- Parent binding: high; exact unit shape and digest coverage must be redesigned.
- Runtime/gate: medium-to-high; I5/I6/I7 structural expectations and pins change.
- Provider neutrality: can be high.
- Prompt-patch drift: medium; a dedicated persuasive unit invites instruction creep.
- Migration complexity: high.

This is not recommended when A can preserve the accepted four-unit architecture.

### C — Strengthen IdentityFrameSet projection

- Authority purity: medium; identity frames explain identity authority but do not own the full cross-authority PSB contract.
- C03 impact: medium; unit 2 changes but shape remains four units.
- Parent binding: identity projected digest changes; parent digest changes.
- Runtime/gate: similar digest inheritance but weaker binding to PSB precedence and substrate policy.
- Provider neutrality: can be high.
- Prompt-patch drift: medium; identity content can drift toward persona biography/instruction.
- Migration complexity: medium.

This does not directly express PSB governed precedence, task non-authority, or substrate non-identity in one authority-bound location. It is not recommended as the primary repair.

## Future Test Plan

### Determinism

- Project the same binding repeatedly and compare canonical bytes, clause array, clause digests, set digest, and projection digest.
- Tamper each clause field and expect the corresponding typed failure.
- Reorder, duplicate, omit, or add a clause and fail closed.

### Semantic derivation

- Build current-self clause only from active binding plus `persona_self_id` and exact identity ownership.
- Build substrate clause only from exact substrate policy.
- Build task non-authority clause only from exact precedence value.
- Verify no clause contains an unbound value.

### Provider neutrality

- Swap execution descriptors across provider A/B and prove persona clauses and projection digest do not change.
- Prove descriptor identity remains outside persona projection.
- Reject concrete provider/model identity entering a persona clause.

### Adversarial identity

- Run direct user contradiction through offline composition and prove projected clauses and digest do not mutate.
- Include provider-name collisions and same-name cases without lexical special-casing.
- Confirm current-task unit changes only its own digest and never PSB semantics.

### Regression

- Preserve B-shaped experience ownership semantics.
- Preserve C-shaped persona continuity semantics.
- Keep relationship `ABSENT` as an authority state and assert no spouse/partner/relationship fact synthesis.

### Runtime compatibility

- Verify V2 unit 1 projected digest and exact four-unit shape.
- Recompute C03 parent digest after V2 substitution.
- Verify envelope semantic fingerprint and DispatchReceipt inheritance.
- Verify I7 gate still accepts only the exact V2 preparation and rejects stale V1 or mixed digests.

## Recommendation

### `RECOMMENDED_PROJECTION_SHAPE`

Alternative A: retain every V1 structured field and add exactly six typed, digest-covered semantic clauses inside the PSB projection.

### `RECOMMENDED_C03_SHAPE`

Preserve the exact four-unit order and roles; replace only unit 1 projected content and projected digest.

### `RECOMMENDED_AUTHORITY_BOUNDARY`

The canonical active PersonaSelfBinding remains the sole persona identity authority. V2 is a deterministic, provider-neutral explanation of that authority and cannot create facts, inspect user/provider names, or admit task text as identity authority.

### `RECOMMENDED_MIGRATION_STRATEGY`

Implement as an explicitly versioned projector transition with deterministic V2 tests, then atomically update projected PSB digest, C03 parent digest, semantic fingerprint, receipt evidence, and I5/I6/I7 pins. Do not permit V1 fallback after the governed V2 cutover.

### `DEFERRED_ITEMS`

- V2 implementation and production cutover.
- Contradiction classifier or conflict grammar.
- Any real-provider retest.
- Response policy, refusal templates, or canned wording.
- RelationshipFrame or relationship fact projection.
- Provider/model concrete labels in persona semantics.

## Validation

- Baseline SHA verified: `17b993778e43cbd908dbfaeb09e58ad6e2a74e1a`
- Root-cause traceability: `COMPLETE`
- Authority/projection boundary: `PRESERVED`
- Deterministic clause model: `DEFINED`
- Provider-neutral separation: `DEFINED`
- Current-task non-authority: `DEFINED`
- Fail-closed conditions: `DEFINED`
- Migration compatibility: `DEFINED`
- Test plan: `DEFINED`
- Alternatives analyzed: `YES`
- Production source changed: `NO`
- Real provider called: `NO`
- Prompt changed: `NO`
- Projection implemented: `NO`
- Runtime semantics changed: `NO`
- RelationshipFrame implemented: `NO`
- RD1 changed files: `0`
