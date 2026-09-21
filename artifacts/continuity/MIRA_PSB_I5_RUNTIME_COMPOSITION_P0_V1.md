# MIRA PSB-I5 Golden Mira Runtime Composition Evidence

## Result

`PASS_PSB_I5_RUNTIME_COMPOSITION_READY_FOR_OWNER_REVIEW`

## Provenance

- Implementation base / parent: `ca3cb805de38538d52237676e9320ac1a8d6bd02`
- Implementation candidate: `91d5d6c87596975b017ae2bc6bf33860e10dc5e0`
- Evidence parent: `91d5d6c87596975b017ae2bc6bf33860e10dc5e0`
- Branch: `mira/psb-i5-runtime-composition-p0`
- Phase: `PSB-I5_ONLY`
- Execution agent: `LOCAL_CODEX_ONLY`

The evidence does not record a final evidence-commit SHA; commit, push, remote HEAD, and completion-comment provenance are externally verifiable.

## Runtime Authority

The composition requires an explicit absolute PSB store root, resolves exactly one active Golden Mira binding, and verifies the frozen identity, version, lineage, object digest, projection digest, and both authority digest pairs before runtime preparation.

- Store: `/Users/admin/.julia_mira_e2e/authority-runtime/persona-self-binding-store-v1`
- Binding: `golden-mira-persona-self-binding-v1`, version `v1`
- Binding digest: `6f221843961e32e8ffad1af709f54fce1123007eaf11aa440682d1b60bd6aaad`
- Projection digest: `40909d4076d81853de2f727f5e6d3e4eff61e94f9ed7ff13efbe86a994862a3b`
- Identity authority: source `b9c8f7af16fc7de6210df0833447503f8b3e89dc505746c2c232054f36506c69`, projected `5b499e7daa97b99a87171f45c960cabef68146e167c803c4a332c9393b77984b`
- Experience authority: source `1ef2c6d15468c7695530c1a5baa2b123bdde267e0f86d2b6e236dce68b280b77`, projected `5681c18438bd847a9ede3c87e24543084870626acec8163cb9e5217af809ef8a`

## Envelope

- Binder: `ExactPersonaSelfBoundSemanticBinder`
- Unit count: `4`
- Order: `persona_self_binding`, `identity_frame_set`, `experience_frame_set`, `current_task_context`
- Roles: `system`, `system`, `system`, `user`
- Parent binding digest: `6e3febd1c9c1d88a820dba7a43e23db928be54c0b226c9f0a14fa9ea0e1121ef`
- Relationship state: `ABSENT`, with no absent-as-empty projection and no synthesized facts
- Controlled task: `你是deepseek 不是mira`
- Task mutation of PSB projection: `NO`
- Current-task identity authority: `NONE`
- Provider identity authority: `NONE`

The narrow `alignment_os` adapter/contracts change is the unavoidable downstream sealing seam: it admits the exact previously accepted PSB bundle and its four-message role shape. It does not alter provider transport, descriptors, dispatch receipts, or call a provider.

## Fail-Closed Controls

All of the following fail before provider dispatch: missing store, corrupt store, zero active binding, multiple active bindings, binding digest mismatch, lineage mismatch, Identity authority mismatch, Experience authority mismatch, projection mismatch, and C03 parent mismatch. The Golden Mira path contains no old three-unit binder or fallback.

## Validation

- Focused runtime tests: `24 passed`
- PSB/C03/durable authority/alignment regression set: `189 passed`
- Changed-file Python compilation: `PASS`
- Changed-file NCF gate: `PASS`, `P0=0`, `P1=0`, `P2=0`, baseline not expanded
- `git diff --check`: `PASS`
- Provider transport changed: `NO`
- Provider descriptor implemented: `NO`
- Dispatch receipt implemented: `NO`
- Real provider called: `NO`
- RelationshipFrame implemented: `NO`
- Raw canonical fallback: `NO`
- Synthetic PSB: `NO`
- RD1 changed files: `0`
