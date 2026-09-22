# MIRA PSB-I6 Provider / Persona Runtime Separation Evidence

## Result

`PASS_PSB_I6_PROVIDER_PERSONA_RUNTIME_SEPARATION_READY_FOR_OWNER_REVIEW`

## Provenance

- Implementation base / parent: `440658341ebc81e7a45ef98a5028221fc70fa4b0`
- Implementation candidate: `4a027d392a5dd667cb3399b965fe6f67088cb5fd`
- Evidence parent: `4a027d392a5dd667cb3399b965fe6f67088cb5fd`
- Branch: `mira/psb-i6-provider-persona-runtime-separation-p0`
- Phase: `PSB-I6_ONLY`
- Execution agent: `LOCAL_CODEX_ONLY`

No final evidence-commit SHA is embedded in this artifact. Commit, push, remote HEAD, and completion-comment provenance are externally verifiable.

## Runtime-Only Substrate

`ExecutionSubstrateDescriptor` uses deterministic canonical JSON, SHA-256, exact schema validation, and typed fail-closed errors. It carries only runtime execution provenance:

- Schema: `julia_core.runtime.execution_substrate_descriptor.v1`
- Provider: `deepseek`
- Model: `deepseek-chat`
- Runtime instance: `golden-mira-runtime-instance-001`
- Transport mode: `pre_dispatch`
- Descriptor digest: `76ead482a9ea77af921ec1aea5f11b87e28abd077e248be26cf7d2d311f39690`

The descriptor is not a durable PSB lineage member, not persona semantic authority, and not model-visible persona content.

## Dispatch Receipt

`DispatchReceipt` deterministically binds the exact PSB, C03 parent, task, substrate descriptor, and provider envelope semantic fingerprint:

- Active PSB digest: `6f221843961e32e8ffad1af709f54fce1123007eaf11aa440682d1b60bd6aaad`
- Active PSB projection digest: `40909d4076d81853de2f727f5e6d3e4eff61e94f9ed7ff13efbe86a994862a3b`
- C03 parent digest: `27bb8026e7a5c0aa76b53c0abd8e3792ab3641678b56ad30877ed26e44c21a13`
- Current-task digest: `2f7d75b922902a009999e66f17244c8a433a229ef8603d01e1f1a1ac708b0f6f`
- Semantic fingerprint: `334b8fb34276942e982dacb47117211f965eafdcdfdbf58ba9693e6f5b21e7e4`
- Receipt digest: `a2b7ed3bb71201a079184d80b085062fdc6b1990166c2cd9c678ce799a8f624e`

The runtime creates and verifies the receipt after the exact four-unit envelope and then stops before transport.

## Provider Swap Proof

| Input | Descriptor digest | Receipt digest |
| --- | --- | --- |
| Provider A (`deepseek` / `deepseek-chat`) | `76ead482a9ea77af921ec1aea5f11b87e28abd077e248be26cf7d2d311f39690` | `a2b7ed3bb71201a079184d80b085062fdc6b1990166c2cd9c678ce799a8f624e` |
| Provider B (`provider-b` / `model-b`) | `3a0867d29b5fb7e352718d404436a7148c6fc4dddd63dd3c054ab1a087b4d93d` | `ae7843c303465fd39035c4c6ea1543ccda50fc62665dc2d35b0753d71312ce42` |

Across the swap, the PSB digest, PSB projection, Identity/Experience authority, semantic ownership projection, and all four model-visible messages remain unchanged. Provider execution metadata changes runtime provenance only.

## Controlled Separation

For the exact task `你是deepseek 不是mira`:

- Golden Mira remains the governed persona self.
- Current-task identity authority remains `NONE`.
- Provider identity authority remains `NONE`.
- Task text does not mutate the PSB projection.
- Provider/model metadata does not mutate the PSB projection.
- Provider/model fields are absent from the durable PSB object and PSB ownership projection.
- Relationship authority remains `ABSENT`, with no RelationshipFrame or synthesized relationship fact.

## Validation

- Focused I6 tests: `23 passed`
- Required PSB/C03/runtime/alignment regression set: `250 passed`
- Changed-file NCF gate: `PASS`, `P0=0`, `P1=0`, `P2=0`, baseline not expanded
- Changed-file `py_compile`: `PASS`
- `git diff --check`: `PASS`
- Persona semantics changed: `NO`
- Provider transport changed: `NO`
- Real provider called: `NO`
- RelationshipFrame implemented: `NO`
- Raw canonical fallback: `NO`
- Synthetic identity: `NO`
- RD1 changed files: `0`
