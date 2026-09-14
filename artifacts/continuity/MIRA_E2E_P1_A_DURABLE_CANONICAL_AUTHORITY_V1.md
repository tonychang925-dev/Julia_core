# MIRA-E2E-P1-A Durable Canonical Authority

## Result

`PASS_READY_FOR_MIRA_E2E_P1_B`

## Source and package

- Base SHA: `5109dde84c0bfd1b76919ed11ae19d55e2618da3`
- P5 admission SHA: `038e5219495fd765bfbcfdbb0a52afb48a730f90`
- P5 artifact: `artifacts/continuity/P5_A1_OWNER_AUTHORIZED_GOLDEN_MIRA_CANONICAL_ADMISSION_V1.json`
- Durable root: `/Users/admin/.julia_mira_e2e/authority`
- Export receipt: `/Users/admin/.julia_mira_e2e/GOLDEN_MIRA_DURABLE_AUTHORITY_EXPORT_V1.json`
- Manifest SHA-256: `97470a2c29714ec26b5bd79dbe2d3c02b121f780f8b210076f28cf7498944cf3`
- Package root digest: `4884f8045d434cf5cc08bf8fbfa783221aba52c919e865f21466be6108fc3703`
- Package files: 13; repeat export was byte-identical.

The one-time owner-gated export serializes the exact frozen 3 Identity and ordered 8 MemoryExperience admission. It performs no admission, canonical write, supersede, retire, semantic normalization, digest regeneration, or lifecycle replay.

## Runtime interface

```python
reader = FilesystemDurableAuthorityReader(authority_root)
identity_repository, memory_repository = reconstruct_from_durable_authority(reader)
```

`FilesystemDurableAuthorityReader` requires an injected absolute `Path`, verifies the manifest and every indexed file, rejects extra/missing/duplicate/reordered records, verifies payload and envelope digests, and validates exact refs, versions, lifecycle, governance, lineage, source provenance, and admission provenance. It contains no fixture path, environment lookup, fallback directory, cwd lookup, or partial recovery.

## Exact canonical set

### Identity

1. `mira-golden:mira-id-cand-001` / `mira-id-cand-001-v0.1-preview` — `7580e0a930dc7f3d5446da2cdd8d1c23cf251e12929fb2f3baa056bd9739dd44`
2. `mira-golden:mira-id-cand-002` / `mira-id-cand-002-v0.1-preview` — `adaa2508c4e475a700c394eb205e278d515dfe014ccdaa4bab3c3e7b7dcd5f3a`
3. `mira-golden:mira-id-cand-003` / `mira-id-cand-003-v0.1-preview` — `0008a5e157347ae9b0dd8600d661ec4a0e3fbd1858673cd04dc7c7b812a96c29`

### Ordered MemoryExperience

1. `golden-mira:GM-CMIR-001` / `v0.2-preview` — `4e29eb74de7f29bbf8d69485a7c18b5dceb06486d7e1d986d668a30c85fb7228`
2. `golden-mira:GM-CMIR-002` / `v0.2-preview` — `e4374452173b144ce48dbefa5299f1ac3dc15cec3615b8e7d528176293536f93`
3. `golden-mira:GM-CMIR-004` / `v0.1-preview` — `ba4edeff89bc8054be19d7a48226fcef74359bc85d17dbd6abea4b754b905f97`
4. `golden-mira:GM-CMIR-006` / `v0.1-preview` — `47636f46d2934eeb66f91c8202e2245c180b7077fddd04ca6445683308b54f2c`
5. `golden-mira:GM-CMIR-008` / `v0.1-preview` — `08c95873446b01949b7aec50ad35ebbe36ce8b5b9ad87aca45c51b627f70c408`
6. `golden-mira:GM-CMIR-011` / `formation-draft-preview` — `3107a3ab38d0fc0d2446752f48bedebf2ee336e3cb8b22811bf3c156247a4ae9`
7. `golden-mira:GM-CMIR-011` / `frozen-final-preview` — `3c31de4d62ecfd5d7857a5a4df85725affa0862d0055b5527d7d80f27fcc8ad8`
8. `golden-mira:GM-CMIR-013` / `v0.2-preview` — `8e2d16304357b7fb72b5b6cb53501be5d8743b3c687d2f0aadf3a9e1e132046c`

## Verification

- Exact export/read/reconstruction roundtrip: PASS.
- Manifest corruption: FAIL_CLOSED.
- Payload digest corruption: FAIL_CLOSED.
- Missing Identity: FAIL_CLOSED.
- Extra Identity: FAIL_CLOSED.
- Wrong MemoryExperience order: FAIL_CLOSED.
- Unexpected duplicate ref: FAIL_CLOSED.
- Non-admitted lifecycle: FAIL_CLOSED.
- Lineage mismatch: FAIL_CLOSED.
- Missing provenance: FAIL_CLOSED.
- Fixture runtime dependency count: 0.

Command: `/opt/miniconda3/bin/pytest -q tests/durable_authority tests/context_admission tests/projection tests/evidence tests/continuity tests/mira_migration`

Result: **258 passed, 0 failed, 0 skipped, 0 warnings**. `git diff --check`: PASS.

NO_CRITICAL_FALLBACK_GATE: **PASS**. The candidate diff produced 0 new P0/P1/P2 findings; the full scan retains one nonfatal historical P2 (`NCF-04 julia_core/runtime/capability_bridge.py:321`). Governance sabotage tests: **4 passed**. The exact historical gate was restored independently in commit `239c0626d97a93829be2e81dd6b2ca37537b7cf8`; `--no-verify` was not used.

## Julia preservation

- PID 629 remained the owner of the `127.0.0.1:18089` listener.
- Product conversation store SHA-256 remained `fbae7e00b8f2275c90c6d769f27d3c1a458cc41528e59127d330d0c4630bcec7`.
- `~/.julia/sessions.json` SHA-256 remained `51702425a4a76f328490788c3890cc3bb2c05276fc57ff38532dbfb0a206fc43`.
- Julia requests: 0; state changed: NO; process restarted: NO; config changed: NO.

## P1-B boundary

P1-B receives only `authority_root`, `FilesystemDurableAuthorityReader`, `reconstruct_from_durable_authority`, and the reconstructed canonical repositories. It must not know P5 fixture paths, migration scripts, or evidence internals.

Blockers: none.
