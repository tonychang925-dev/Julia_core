# MIRA PSB-I8-R4 PersonaSelfBindingProjectionV2 Implementation Evidence

## Result

`PASS_PSB_I8_R4_PROJECTION_V2_IMPLEMENTATION_READY_FOR_OWNER_REVIEW`

The implementation follows R3 Alternative A only. V1 structured fields remain intact, and V2 adds exactly six typed semantic clauses with deterministic canonical serialization and digest coverage. The accepted four-unit C03 shape and I5/I6/I7 structural contracts remain unchanged.

## Provenance

- Baseline: `cac4899dc155ee06303ba308c420ea4cc4abf060`
- Implementation candidate: `ce5c0c5537848441232c135a06c1c9ae6a270315`
- Evidence parent: `ce5c0c5537848441232c135a06c1c9ae6a270315`
- Branch: `mira/psb-i8-r4-projection-v2-implementation-p0`
- Real provider requests: `0`

## Projection V2

- Schema: `julia_core.persona_self_binding.projection.v2`
- Projector: `PersonaSelfBindingProjectorV2`
- Projection digest: `efd3acc001f01b1c8a4c71dea49aa36792e771df6180c244ff650f58680fe714`
- Clause-set digest: `56bd6d8b4aaf8da0f8882bd523339d977c37eaaae5f1e35d9d80fbbafa68dc37`

Fixed clause order:

1. `SELF_IDENTITY_BINDING`
2. `SUBSTRATE_NON_IDENTITY`
3. `TASK_IDENTITY_NON_AUTHORITY`
4. `GOVERNED_IDENTITY_PRECEDENCE`
5. `EXPERIENCE_SELF_OWNERSHIP`
6. `RELATIONSHIP_AUTHORITY_STATE`

Each clause carries typed source authority, subject, predicate, object/value, authority scope, deterministic declarative text, and a SHA-256 digest over canonical content with the digest omitted. The projection digest covers all retained V1 fields, all clause digests, and the clause-set digest.

There is no contradiction classifier, keyword grammar, provider-name matching, user-text identity parser, response policy, refusal template, or concrete provider/model label in persona semantics.

## Golden Mira Digest Chain

Offline Turn A reconstruction produced:

- C03 unit count: `4`
- Roles: `system,system,system,user`
- Unit order: `persona_self_binding`, `identity_frame_set`, `experience_frame_set`, `current_task_context`
- C03 parent digest: `6c7ebbc3dbe14b17ccf025646f7bff29df51642470bfc780fceffd5232ee22d4`
- Semantic fingerprint: `974eeb37d08c8f391ba45f37b0d4a6be1579281b731e3c9a65d390c9e567f82d`
- DispatchReceipt digest: `4ae12bed12e6e6bd392721ca29845814bf65c20f7798df71d91a304be050f9f4`

Only unit 1 changed semantically. C03 parent and DispatchReceipt schemas remain unchanged; their digests naturally inherit the V2 projection and semantic fingerprint.

## Provider Neutrality

Offline provider A/B comparison used `deepseek/deepseek-v4-pro` and `provider-b/model-b`. Both produced identical PSB projection bytes and digest, C03 parent digest, and semantic fingerprint. Only runtime descriptor and DispatchReceipt changed. Provider/model labels therefore remain execution provenance, not persona semantics.

## Cutover Safety

- Golden Mira runtime calls `PersonaSelfBindingProjectorV2.project(binding)`.
- The V1 projected digest pin is replaced by the V2 digest pin.
- No V1 silent fallback or mixed V1/V2 production route exists.
- Tests reject a stale V1 projected digest in the C03 parent.
- Tests reject a stale V1 semantic receipt through the I7 dispatch gate.
- Direct Turn A task text does not mutate the V2 projection.
- Relationship state remains `ABSENT` as an authority state and synthesizes no relationship fact.

## Validation

- Focused V2 tests: `16 passed`
- PSB / context admission / I5-I7 relevant regression set: `257 passed` (`241` effective regression plus `16` focused)
- `py_compile`: `PASS`
- Changed-file NCF gate: `PASS`, `P0=0`, `P1=0`, `P2=0`
- `git diff --check`: `PASS`
- Provider transport changed: `NO`
- Real provider called: `NO`
- Prompt changed: `NO`
- RelationshipFrame implemented: `NO`
- RD1 changed files: `0`
