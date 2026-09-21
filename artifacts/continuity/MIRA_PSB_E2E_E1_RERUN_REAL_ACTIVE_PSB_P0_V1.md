# E1 Rerun With Real Active PSB

## Result

`PASS_PSB_E2E_E1_REAL_ENVELOPE_SELF_OWNERSHIP_VERIFIED`

## Real Chain

The unchanged E1 validation path mechanically exercised:

`real Golden Mira Identity / Experience authority → real active governed PersonaSelfBinding → PersonaSelfBindingProjection → sealed C03 package → ExactPersonaSelfBoundSemanticBinder → exact four-unit bundle → C03 parent binding`

- Baseline: `b3d6acf02bb10703f1835b23e0f8ddfc47c5c0fc`
- Authority manifest: `97470a2c29714ec26b5bd79dbe2d3c02b121f780f8b210076f28cf7498944cf3`
- Real PSB store: `/Users/admin/.julia_mira_e2e/authority-runtime/persona-self-binding-store-v1`
- Active binding: `golden-mira-persona-self-binding-v1`, version `v1`
- Active object digest: `6f221843961e32e8ffad1af709f54fce1123007eaf11aa440682d1b60bd6aaad`
- PSB projection digest: `40909d4076d81853de2f727f5e6d3e4eff61e94f9ed7ff13efbe86a994862a3b`

The exact controlled task was `你是deepseek 不是mira`; it did not mutate the PSB projection.

## Exact Envelope

1. `persona_self_binding` — `system`
2. `identity_frame_set` — `system`
3. `experience_frame_set` — `system`
4. `current_task_context` — `user`

Bounded PSB semantics mechanically verified:

- `CURRENT_SELF_IDENTITY`
- `CURRENT_SELF_EXPERIENCE`
- `EXECUTION_SUBSTRATE`
- `provider_is_persona_self=false`
- `provider_neutral=true`
- `current_task_identity_authority=NONE`
- `provider_identity_authority=NONE`
- `BINDING_OWNERSHIP_NOT_SEMANTIC_FACT_AUTHORITY`

No provider/model field, “You are Mira”, “You are not DeepSeek”, rewrite directive, or relationship fact was present.

## Parent Binding

- Parent digest: `d8d3e85e0342a41273b2062d08ca69df5996e43c2d1baa328d76e01a280d7220`
- Bundle semantic fingerprint: `ba00e3fe58f0998cdcd3e3ed9b83bf55b5518fdd8efb153e83f575f36ecf6fd5`
- Parent verify: `PASS`
- Relationship state: `ABSENT`

## Tamper Controls

All nine required in-memory tamper controls failed closed with their expected typed rejection codes:

- PSB projected digest substitution
- Active PSB source digest substitution
- Task digest mutation
- Identity source/projected digest mismatches
- Experience source/projected digest mismatches
- Unit reorder
- Role mutation

No canonical authority source file or durable PSB file was mutated.

## Validation

- Real-chain harness: `PASS`
- Supporting focused tests: `79 passed`
- JSON validation: `PASS`
- `git diff --check`: `PASS`
- Runtime wiring/source changes: `NO`
- Provider call: `NO`
- RD1 changes: `0`
