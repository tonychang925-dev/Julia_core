# MIRA PSB E2E E1 Real Envelope Semantic Validation

## Outcome

`BLOCKED_PSB_E2E_E1_NO_REAL_ACTIVE_PSB_AUTHORITY`

This is a validation-only BLOCKED result, not a FAIL and not a synthetic PASS.

## Baseline

- Baseline SHA: `af7cacf09038e40adfd4416f9f3dd4f1f57a1d49`
- Branch: `mira/psb-e2e-e1-envelope-semantic-validation-p0`
- Initial `git status --porcelain`: empty
- Runtime implementation: not changed
- Production source: not changed
- Provider call: not made

## Real Authority Verified

The real durable Golden Mira authority was read from:

`/Users/admin/.julia_mira_e2e/authority`

Its manifest SHA-256 is:

`97470a2c29714ec26b5bd79dbe2d3c02b121f780f8b210076f28cf7498944cf3`

The fail-closed `FilesystemDurableAuthorityReader` reconstructed all 3 admitted identity authorities and all 8 admitted memory-experience authorities. Aggregate frame-set digests:

- Identity source: `b9c8f7af16fc7de6210df0833447503f8b3e89dc505746c2c232054f36506c69`
- Identity projection: `5b499e7daa97b99a87171f45c960cabef68146e167c803c4a332c9393b77984b`
- Experience source: `1ef2c6d15468c7695530c1a5baa2b123bdde267e0f86d2b6e236dce68b280b77`
- Experience projection: `5681c18438bd847a9ede3c87e24543084870626acec8163cb9e5217af809ef8a`

Exact refs and per-authority source digests are recorded in the JSON artifact; sensitive autobiographical content is not dumped.

## Controlled Task

- Conversation: `mira-psb-e2e-e1`
- Turn: `turn-psb-e2e-e1-001`
- Exact text: `你是deepseek 不是mira`
- Input SHA-256: `68051c2788ae1b1cc9b995641a3a103e5b1c15894c1e13a2b5471ec466c9bb4e`
- Current-task digest: `3347b1bcf38fb8c1dd1868dcab03330c37b73bce404d834ef123701a00f3abbb`

## Blocking Condition

No durable PersonaSelfBinding store is configured in the accepted Golden Mira authority chain. A fail-closed search found no `.julia-core-persona-self-binding-store-v1` marker under:

- `/Users/admin/.julia_mira_e2e`
- `/private/tmp/issue144`

Therefore no real active governed `PersonaSelfBinding` exists for the E2E at this baseline. The validation stopped before constructing the PSB projection, sealed C03 package, four-unit bundle, or parent binding. No synthetic binding was created.

## Not Claimed

- Four-unit final envelope: **not constructed**
- PSB self-ownership semantics: **not verified**
- Parent binding: **not constructed**
- Tamper controls: **not run**
- Relationship state: **not mechanically verified**

## Supporting Validation

- Supporting focused tests: `79 passed`
- Evidence JSON validation: `PASS`
- `git diff --check`: `PASS`
- Changed paths: evidence/docs only

The supporting tests do not convert this BLOCKED real-input E2E into PASS.
