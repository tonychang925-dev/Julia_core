# Real Golden Mira PSB Bootstrap & Governance Admission

## Result

`PASS_REAL_GOLDEN_MIRA_PSB_BOOTSTRAP_ADMISSION_READY_FOR_OWNER_REVIEW`

## Provenance

- Baseline: `f2d947634a6445218a6cedf2573cda676c449754`
- Branch: `mira/psb-real-bootstrap-admission-p0`
- Execution: `LOCAL_CODEX_ONLY`
- Real authority root: `/Users/admin/.julia_mira_e2e/authority`
- PSB store root: `/Users/admin/.julia_mira_e2e/authority-runtime/persona-self-binding-store-v1`
- Store marker: `.julia-core-persona-self-binding-store-v1`

The PSB store is a deterministic sibling in the approved isolated Mira authority-runtime hierarchy. It is not nested inside the immutable authority package because `FilesystemDurableAuthorityReader` validates an exact package file set; adding a durable store beneath that package would invalidate the accepted reader contract.

## Real Authority

Pre- and post-cutover authority manifest SHA-256 are identical:

`97470a2c29714ec26b5bd79dbe2d3c02b121f780f8b210076f28cf7498944cf3`

The exact reconstructed aggregate frame sets matched E1:

- Identity: 3 records; source `b9c8f7af16fc7de6210df0833447503f8b3e89dc505746c2c232054f36506c69`; projection `5b499e7daa97b99a87171f45c960cabef68146e167c803c4a332c9393b77984b`
- Experience: 8 records; source `1ef2c6d15468c7695530c1a5baa2b123bdde267e0f86d2b6e236dce68b280b77`; projection `5681c18438bd847a9ede3c87e24543084870626acec8163cb9e5217af809ef8a`

Independent aggregate authority IDs are not persisted by the existing contracts. The governed references therefore use the exact production aggregate frame-set digests as authority IDs and record that derivation. No substitute authority set was used.

## Governed Binding

- `persona_self_id`: `golden-mira`, derived from the existing durable authority manifest
- `binding_id`: `golden-mira-persona-self-binding-v1`
- Version: `v1`
- Lineage: `golden-mira-persona-self-binding`
- Lifecycle: `ADMITTED_ACTIVE`
- Object digest: `6f221843961e32e8ffad1af709f54fce1123007eaf11aa440682d1b60bd6aaad`
- Projection digest: `40909d4076d81853de2f727f5e6d3e4eff61e94f9ed7ff13efbe86a994862a3b`

Governance history is exactly:

1. `PROPOSE_BINDING`
2. `REVIEW_BINDING`
3. `ADMIT_AND_ACTIVATE`

All events are owner-governance provenance; no user utterance or provider output is provenance.

## Invariants

- Pre-existing PSB store: `NO`
- Pre-existing active bindings: `0`
- Post active bindings: `1`
- Durable records: `3` (`DRAFT`, `GOVERNANCE_REVIEW`, `ADMITTED_ACTIVE`)
- `resolve_active("golden-mira")`: exact active object
- Inventory: deterministic
- Fresh-process reload and projection verify: `PASS`
- Focused supporting tests: `65 passed`
- Relationship state: `ABSENT`; authority is `null`

`ABSENT` means only that no RelationshipFrameSet authority is currently bound. No spouse, partner, 老公, or other relationship fact was synthesized.

## Scope

- Runtime wiring: unchanged
- Provider transport/provider call: unchanged / not called
- RelationshipFrame: not implemented
- Synthetic identity/experience/relationship: not used
- Fallback or bootstrap regeneration: not used
- RD1 changes: `0`
- Repository changes: evidence/docs only
