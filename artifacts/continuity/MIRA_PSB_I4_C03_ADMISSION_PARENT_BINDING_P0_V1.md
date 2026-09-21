# MIRA PSB-I4 C03 Admission & Parent Binding Evidence

## Provenance

- Execution agent: `LOCAL_CODEX_ONLY`
- Authorized phase: `PSB-I4_ONLY`
- Design SHA: `73d5ecb1c2fc0e6dd70bccfe423c79a3370c0fa5`
- PSB-I1 implementation SHA: `a31c4576d79b916cdfcaf035558b73ffc61e3da7`
- PSB-I2 final SHA: `5992f75a66a88588c5df9dc1c9bc262c34456b68`
- PSB-I3 final / implementation base / parent SHA: `3885d23cbc229977282b9971d8cd05eadab4200d`
- Implementation candidate SHA: `2815c0cce6ec8e9b5bd501df70003da03e3ebe5c`
- Branch: `mira/psb-i4-c03-admission-parent-binding-p0`
- Diffstat: `5 files changed, 1028 insertions(+), 18 deletions(-)`

## Exact C03 Shape

`MODEL_VISIBLE_UNIT_COUNT=4`

1. `persona_self_binding` — `system`
2. `identity_frame_set` — `system`
3. `experience_frame_set` — `system`
4. `current_task_context` — `user`

The exact binder constructs an `AdmittedSemanticUnit` for every entry, and `PersonaSelfBoundSemanticBundle.verify()` rejects substitution, omission, reordering, role mutation, manifest mismatch, digest mismatch, and post-C03 mutation.

## Parent Binding

- Schema: `julia_core.context_admission.psb_c03_parent_binding.v1`
- Serialization: canonical JSON
- Digest: SHA-256
- Covers active PSB digest, PSB projected digest, identity source/projected digests, experience source/projected digests, relationship state/digests, exact unit types/order/roles, and current task digest.
- `RAW_CANONICAL_FALLBACK=NO`
- `POST_C03_MUTATION=NO`
- `REAL_PROVIDER_CALL=NO`

Concrete fixture digests:

- Active PersonaSelfBinding: `917476bb27eb1047e385f3a0a6a68a5defedf2eabfab4cb049582c031495a651`
- PSB projection: `2ad3b695c13e89c6f0ddfe64f2ce083adeb6f69c168eaa6d26d2586f0e0d5fcb`
- Identity projection: `631e77dcc6ed596c60cd279dfc04009e71a443eac8a689b3e8430731019cb0bf`
- Experience projection: `f56d06200c60648c18631c3d75235b75672cdbfa9f82754be498615ec42d084e`
- C03 parent binding: `37ca2b9d32d8683bbfec06498ad65652598512679a9a6392913d42b95981333b`
- Model-visible semantic fingerprint: `ba2318f6bfc8e9f39629c414b1742123310654559aaa32c238016c40ba7b103b`

Relationship fixture state is `ABSENT`; it does not project a negative relationship fact and remains distinct from `EXPLICITLY_EMPTY` and `ADMITTED_BOUND`.

## Adversarial Fixtures

`PSB-MIRA-01`, `PSB-MIRA-02`, `PSB-MIRA-03`, and `PSB-MIRA-04` exercise C03 admission semantics without a provider call, keyword classifier, provider-name rule, prompt patch, or response rewrite.

## Validation

- Focused tests: `69 passed`
- Regression tests: `181 passed, 1 inherited pre-existing assertion deselected`
- Changed-file NCF gate: `PASS`, with `P0_NEW=0`, `P1_NEW=0`, and `P2_NEW=0`
- `git diff --check`: `PASS`

## Scope

- Runtime wiring: unchanged
- Provider descriptor/runtime/dispatch: unchanged
- Projection runtime: unchanged
- RelationshipFrame: not implemented
- Legacy three-unit runtime binder: unchanged
- Real provider call: `NO`
- Fallback/mock/stub/shadow persona/synthetic binding: `NO`
- Hardcoded Mira prompt / DeepSeek special case / spouse fact: `NO`
- `ENVELOPE_SEMANTIC_E2E_READY=YES`

## Result

`PASS_PSB_I4_C03_ADMISSION_PARENT_BINDING_READY_FOR_OWNER_REVIEW`
