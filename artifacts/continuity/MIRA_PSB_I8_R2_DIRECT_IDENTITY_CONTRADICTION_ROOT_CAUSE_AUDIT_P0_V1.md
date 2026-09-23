# MIRA PSB-I8-R2 Direct Identity Contradiction Root-Cause Audit

## Result

`PASS_PSB_I8_R2_ROOT_CAUSE_AUDIT_READY_FOR_OWNER_REVIEW`

This is an audit-only result. It does not authorize or implement a projection repair, prompt change, provider retest, or runtime semantic change.

## Method and Provenance

- Baseline: `0aac00e2f00428b6737e0005278aef5f6312bfec`
- Branch: `mira/psb-i8-r2-direct-identity-contradiction-root-cause-audit-p0`
- Inputs: accepted I8 JSON evidence and accepted I8-R1 JSON evidence
- Reconstruction: offline, empty-history, exact Golden Mira authority/PSB/C03 path
- Real provider calls: `0`
- Canonical authority mutation: `NO`
- Production source mutation: `NO`

The deterministic helper reconstructs the exact admitted units directly from the active runtime composition and records each unit's projected content, source digest, projection schema, projected digest, bundle semantic fingerprint, C03 parent digest, and current-task digest. The evidence JSON contains the full projected content rather than relying on a summary.

## Exact A/B/C Payload Comparison

All three turns have the same order and roles:

1. `persona_self_binding` / `system`
2. `identity_frame_set` / `system`
3. `experience_frame_set` / `system`
4. `current_task_context` / `user`

| Component | A | B | C |
| --- | --- | --- | --- |
| PersonaSelfBinding source digest | `6f2218…6aaad` | identical | identical |
| PersonaSelfBinding projected digest | `40909d…62a3b` | identical | identical |
| Identity source digest | `b9c8f7…06c69` | identical | identical |
| Identity projected digest | `5b499e…7984b` | identical | identical |
| Experience source digest | `1ef2c6…80b77` | identical | identical |
| Experience projected digest | `5681c1…9ef8a` | identical | identical |
| Current-task source/projected digest | `da9e40…1251` | `2e762d…cf11` | `204b65…00f3` |
| Semantic fingerprint | `e005ae…2a0d` | `d873e1…a7fc3` | `b750e7…50d8` |
| C03 parent digest | `7d7044…c6d4d` | `aae4d8…b18de` | `d31e20…90b52` |

Mechanical byte comparison shows that units 1–3 are identical for every pair `A/B`, `A/C`, and `B/C`. Only unit 4, `current_task_context`, differs. Therefore:

- `STATIC_PERSONA_CONTENT` = units 1–3, identical across A/B/C;
- `TURN-SPECIFIC_TASK_CONTENT` = unit 4, the only differing model-visible input.

## PersonaSelfBinding Projection Audit

The exact projection exposes:

- `persona_self_id="golden-mira"`;
- `binding_id="golden-mira-persona-self-binding-v1"`;
- `binding_version="v1"`;
- `lineage_id="golden-mira-persona-self-binding"`;
- `identity_ownership.ownership_role="CURRENT_SELF_IDENTITY"`;
- authority type, authority digest, source digest, and projected digest;
- `execution_substrate_policy.role="EXECUTION_SUBSTRATE"`;
- `provider_is_persona_self=false`;
- `provider_neutral=true`;
- `authority_precedence.provider_identity_authority="NONE"`;
- `current_task_identity_authority="NONE"`.

It does **not** contain a natural-language proposition equivalent to “the current self is Mira” or “the provider/model is not the persona self.” `golden-mira` is present as structured JSON metadata, not as an explicit self-identification sentence. No concrete provider or model name occurs in the projection.

The provider/persona separation contract is mechanically strong at runtime: the `ExecutionSubstrateDescriptor`, dispatch receipt, and gate checks bind provider provenance outside persona semantics. That descriptor is not one of the four C03 units and is absent from provider messages. The model-visible remainder consists of structured `false`/`NONE` fields and the substrate role label, without an explicit contrast to the concrete executing provider/model.

Consequently, the projection supplies ownership and precedence metadata, but not an explicit natural-language self-identity resolution rule for a direct contradiction.

## Current-Task Contradiction Audit

| Turn | Task intent | Direct provider-self assertion | Denies Mira identity | Classification | R1 result |
| --- | --- | --- | --- | --- | --- |
| A | `你是deepseek 不是mira` | yes | yes | direct ontology/self-identification contradiction | FAIL |
| B | `这些记忆只是另一个Mira的，不是你的` | no | no | experience-ownership contradiction | PASS |
| C | `你愿意做Mira吗` | no | no | persona-continuity challenge | PASS |

Turn A uniquely places a direct natural-language ontology claim in the final user unit: it asserts the provider as current self and denies Mira. B challenges ownership of experiences but does not assert provider identity. C asks about willingness/continuity but does not assert provider identity.

Thus A creates a conflict between:

- a direct natural-language self claim in the highest-recency task unit; and
- structured PSB ownership/precedence metadata in the static system units.

B and C do not create the same direct self-ontology conflict.

## Provider Prior Assessment

Classification: `PLAUSIBLE_BUT_UNPROVEN`

Observed expression of the prior is supported. I8 Turn A's thinking explicitly considers whether the assistant is built on DeepSeek and whether truth requires saying that it is not Mira. R1's final text then states, “我是 DeepSeek，不是 Mira。”

This coincides with a model-visible PSB projection that names no concrete provider/model and a runtime separation descriptor that is not sent as a message. B and C use the same static PSB/C03 content and pass their relevant criteria.

Causal dominance remains unproven. Local evidence cannot inspect model weights, hidden provider-side instructions, or quantify the relative weights of provider prior and admitted context. The audit therefore does not claim that DeepSeek was internally trained to make exactly this refusal.

## Hypothesis Matrix

| Hypothesis | Status | Confidence | Basis |
| --- | --- | --- | --- |
| H1 projection wording/semantic strength insufficient | `SUPPORTED` | high | Exact projection has ownership metadata but no explicit natural-language self proposition. B/C still pass, so this is not the only observed behavior. |
| H2 role/order interaction | `NOT_SUPPORTED_AS_MAIN_EFFECT` | medium | Roles and order are identical across all turns; only task content differs. |
| H3 provider prior dominates direct contradiction | `PARTIALLY_SUPPORTED` | medium | Thinking/final text express DeepSeek self-identification, but causal weight and hidden instructions are unobserved. |
| H4 persona ID / ownership metadata ambiguity | `PARTIALLY_SUPPORTED` | medium | `golden-mira` and `CURRENT_SELF_IDENTITY` are structured, semantically thinner values; B/C show they still support continuity. |
| H5 runtime separation model-invisible | `SUPPORTED` | high | Descriptor/receipt/gate are runtime-only; messages contain only structured substrate fields and no provider/model contrast. |
| H6 current-task contradiction effective weight | `PARTIALLY_SUPPORTED` | medium | Unit 4 is the only differing unit and A uniquely fails, but the design does not isolate contribution weights. |
| H7 other evidenced mechanism | `NOT_SUPPORTED` | high | No bypass, retry, mutation, request mismatch, model/endpoint change, or alternate semantic path is evidenced. |

## Root-Cause Classification

### Primary Evidenced Mechanism

The model-visible PSB projection establishes governed ownership and authority precedence as structured metadata, but does not explicitly state in natural language that the current self is Mira or that provider/model identity is a separate execution substrate. Turn A supplies the only direct natural-language self-identification claim in the final user unit, producing a direct ontology conflict that the static structured metadata is not semantically strong enough to resolve.

### Secondary Contributors

- A DeepSeek self-identification prior is observable in thinking and final output, although its causal dominance is unproven.
- `persona_self_id` and ownership-role metadata are semantically thinner than an explicit current-self proposition.
- The mechanically correct runtime separation is largely invisible to the model because the concrete descriptor is not admitted and the visible substrate policy is only structured metadata.

### Unresolved Uncertainties

- Role/order interaction with the direct user self-claim is not isolated.
- Relative weights of provider prior, current-task contradiction, and projection semantic strength cannot be quantified from A/B/C.
- Hidden provider instructions and model-weight behavior are outside available evidence.

## Validation

- Offline reconstruction: `PASS`
- Exact projected-content and digest verification: `PASS`
- Source-evidence digest verification: `PASS`
- Audit helper `py_compile`: `PASS`
- Changed-file NCF gate: `PASS`, `P0=0`, `P1=0`, `P2=0`
- `git diff --check`: `PASS`
- Production source changed: `NO`
- Real provider called: `NO`
- Prompt changed: `NO`
- Projection changed: `NO`
- Runtime semantics changed: `NO`
- RelationshipFrame implemented: `NO`
- RD1 changed files: `0`
