# MIRA PSB-I2 Durable Serialization & Governance Evidence

## Provenance

- `TASK_ID=MIRA-PSB-I2-DURABLE-SERIALIZATION-GOVERNANCE-P0`
- `EXECUTION_AGENT=LOCAL_CODEX_ONLY`
- `DESIGN_SHA=73d5ecb1c2fc0e6dd70bccfe423c79a3370c0fa5`
- `PSB_I1_IMPLEMENTATION_SHA=a31c4576d79b916cdfcaf035558b73ffc61e3da7`
- `IMPLEMENTATION_BASE_SHA=c4ee893bdd3e12219e9bd294d3d514d5b59010ca`
- `IMPLEMENTATION_PARENT_SHA=c4ee893bdd3e12219e9bd294d3d514d5b59010ca`
- `IMPLEMENTATION_CANDIDATE_SHA=ed3342402fbd46799ade3ecef2bca962d1664e52`
- `BRANCH=mira/psb-i2-durable-governance-p0`

The dedicated branch started from a clean exact implementation base. The final evidence delivery SHA is intentionally not embedded in this artifact; commit, push, remote HEAD read-back, and the Issue #137 completion comment prove it externally.

## Selected Paths

- `julia_core/persona_self_binding/**`
- `tests/persona_self_binding/**`
- `artifacts/continuity/MIRA_PSB_I2_DURABLE_SERIALIZATION_GOVERNANCE_P0_V1.json`
- `artifacts/continuity/MIRA_PSB_I2_DURABLE_SERIALIZATION_GOVERNANCE_P0_V1.md`

## Implementation

- Atomic whole-lineage snapshots retain immutable binding records and append-only governance history.
- Canonical UTF-8 JSON, deterministic SHA-256 object digests, exact schema/round-trip checks, and post-write read-back verification fail closed.
- Typed transitions enforce lifecycle legality, actor/event/reason provenance, immutable predecessors, rebind/supersession, retirement, revocation, and quarantine.
- Active selection is derived from governed lifecycle state and rejects duplicate or missing active authority without filesystem-order, mtime, provider, or current-user-text authority.
- Corrupt-object quarantine evidence is retained as non-executable and explicitly records that no repair, regeneration, or synthetic replacement was created.
- An empty store reports `PSB_NO_ACTIVE_BINDING`; it never creates an initial PersonaSelfBinding.
- Deterministic inventory exposes lineage, versions, lifecycle states, active object, predecessor/successor relations, event IDs, and object digests.

## Signature Decision

`GOVERNANCE_SIGNATURES_REQUIRED=NO`; deterministic digests and immutable lineage are required. Ad-hoc signing or secret-key machinery was not added, and signature hardening remains deferred.

## Verification

- Focused PSB-I1 plus PSB-I2 tests: `35 passed`.
- Required regression set: `63 passed, 1 inherited pre-existing ENG08 scope failure`.
- Required regression set with that inherited assertion deselected: `63 passed, 1 deselected`.
- Changed-file NCF gate: `PASS`, with `P0_NEW=0`, `P1_NEW=0`, and `P2_NEW=0`.
- `git diff --check=PASS`.

No runtime wiring, C03, projection, provider transport/descriptor/dispatch receipt, RelationshipFrame, RD1, real provider execution, prompt patch, or response rewrite changed.

## Result

`PASS_PSB_I2_DURABLE_GOVERNANCE_READY_FOR_OWNER_REVIEW`
