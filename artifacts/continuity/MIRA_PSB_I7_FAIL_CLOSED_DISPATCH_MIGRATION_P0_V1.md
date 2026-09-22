# MIRA PSB-I7 Fail-Closed Dispatch Migration Evidence

## Result

`PASS_PSB_I7_FAIL_CLOSED_DISPATCH_MIGRATION_READY_FOR_OWNER_REVIEW`

## Provenance

- Implementation base / parent: `9a1069427f2394632e3c6e26c67fa2a478de52de`
- Implementation candidate: `b073fe42b618061af12abb02038c469fb6fa4c5d`
- Evidence parent: `b073fe42b618061af12abb02038c469fb6fa4c5d`
- Branch: `mira/psb-i7-fail-closed-dispatch-migration-p0`
- Phase: `PSB-I7_ONLY`
- Execution agent: `LOCAL_CODEX_ONLY`

No final evidence-commit SHA is embedded. Commit, push, remote HEAD, and completion-comment provenance are externally verifiable.

## Dispatch Gate

`GoldenMiraDispatchGate.authorize(...)` accepts only exact `ProviderDispatchPreparation` and verifies the exact PSB-bound C03 bundle, parent binding, pinned active PSB digest, runtime substrate descriptor, dispatch receipt, runtime instance, and false pre-gate transport state. It emits only `GoldenMiraDispatchAuthorization`, a typed runtime-only authorization object with no persona semantic authority.

`GoldenMiraTransportBoundary.seal(...)` accepts only that authorization and returns `GoldenMiraSealedTransport`; it invokes no provider transport.

Controlled provenance:

- Active PSB: `6f221843961e32e8ffad1af709f54fce1123007eaf11aa440682d1b60bd6aaad`
- Active PSB projection: `40909d4076d81853de2f727f5e6d3e4eff61e94f9ed7ff13efbe86a994862a3b`
- C03 parent: `ab3cc089366c16287960e18a84315edfc8edadfdb95dc2641bcf1a8ef31b0b7f`
- Task: `1ce351ac0ff69e781d50d0096fedb5ca0623afb25890e2d75ec4e28f9a05612c`
- Descriptor: `76ead482a9ea77af921ec1aea5f11b87e28abd077e248be26cf7d2d311f39690`
- Receipt: `7c9a600f43fa4185cc2a6c9e4c10c6a6a9998d8ae0fcbf5744dc928aaeea22ac`
- Gate authorization: `60f68d5d81c11cb5cec3e313c024c5f9b55ee811445af6d0dda3d3839f388290`
- Semantic fingerprint: `7a6151feda4f889c06b8827e60c4cbab1cbd20757216d823d0e6f7204a31016d`

## Non-Bypassability

A static AST/source proof verifies that the only Golden Mira composition method calling the transport boundary is `dispatch_to_transport_boundary`, and that method must call `prepare_provider_dispatch`, `GoldenMiraDispatchGate.authorize`, then `GoldenMiraTransportBoundary.seal`. `prepare_provider_envelope()` remains non-dispatch-capable and contains no transport seam call. The old 3-unit binder is absent.

Dynamic sabotage tests reject raw objects, raw envelopes, legacy 3-unit bundles, unreceipted preparations, invalid/stale descriptors, provider mismatches, wrong PSB/parent/task/descriptor/fingerprint receipts, provider metadata projection injection, and pre-marked transport state.

## Provider Swap

Both provider A and provider B pass the gate. Descriptor, receipt, and authorization digests change; the PSB digest, PSB projection, Identity/Experience authority, and four model-visible messages remain unchanged.

## Validation

- Focused I7 tests: `19 passed`
- Required regression set: `270 passed`
- Changed-file NCF gate: `PASS`, `P0=0`, `P1=0`, `P2=0`
- Changed-file `py_compile`: `PASS`
- `git diff --check`: `PASS`
- Persona semantics changed: `NO`
- Provider transport changed: `NO`
- Real provider called: `NO`
- RelationshipFrame implemented: `NO`
- Legacy 3-unit fallback present: `NO`
- Raw envelope dispatch path present: `NO`
- RD1 changed files: `0`
