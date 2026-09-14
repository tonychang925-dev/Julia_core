# MIRA-E2E-P1-B — Golden Mira Isolated Runtime Composition

## Result

`PASS_READY_FOR_MIRA_E2E_P1_C`

- Base: `08b8002b2973bf88dabe729d58e10d6ccab2968d`
- Composition entry point: `compose_golden_mira_runtime(...)`
- Runtime implementation: `julia_core/runtime/mira_composition.py`
- Tests: `tests/runtime/test_mira_composition.py`

## Composition

The isolated composition requires an absolute authority root, absolute conversation-store path, and an exact `MiraRuntimeShaPins` value. Core and Assistant pin mismatches fail before reconstruction. The runtime does not execute git; a launcher supplies expected and observed values.

The authority path is exactly:

`FilesystemDurableAuthorityReader` → `reconstruct_from_durable_authority` → exact repositories → `CanonicalSemanticAuthoritySource` → ordered `IdentityFrameSet` and `ExperienceFrameSet` → production C03 v3 `ExclusiveAdmissionGate` → `ExactAdmittedSemanticBinder` → `JuliaAssistantRuntime.prepare` → `ProviderExecutionEnvelope`.

Projected frames receive the canonical source-ref/source-digest binding required by the frozen C03 production gate. No canonical payload, digest, lifecycle, governance, or lineage value is rewritten.

## Canonical Set

- Persona: `golden-mira`
- Identity records: 3
- Ordered MemoryExperience records: 8
- Identity order: `mira-id-cand-001`, `mira-id-cand-002`, `mira-id-cand-003`
- Memory order: `GM-CMIR-001`, `GM-CMIR-002`, `GM-CMIR-004`, `GM-CMIR-006`, `GM-CMIR-008`, `GM-CMIR-011/formation-draft-preview`, `GM-CMIR-011/frozen-final-preview`, `GM-CMIR-013`

## Isolation and Boundaries

- Conversation persistence injects `LegacyJsonConversationRepository(conversation_store_path)`.
- No cwd fallback and no implicit `data/conversations.json`.
- No `JuliaSession`, Julia narrative bootstrap, or Julia persona feature-store dependency.
- No provider network call and no fake provider response.
- The envelope-preparation test disables `socket.socket` and still reaches `ProviderExecutionEnvelope`.
- Existing `ConversationRuntime` and forbidden authority/projection contracts are unchanged.

## Verification

- Focused P1-B tests: 9 passed / 0 failed / 0 skipped / 0 warnings.
- Mandatory relevant regression: 267 passed / 0 failed / 0 skipped / 0 warnings.
- `NO_CRITICAL_FALLBACK_GATE`: PASS, 0 new P0/P1 and one known nonfatal P2.
- `git diff --check`: PASS.
- Full `tests/runtime` audit has 17 failures at both base and candidate, with candidate adding exactly the 9 passing P1-B tests; those legacy failures are pre-existing and outside this task.

## Julia Preservation

- PID 629 remained the `127.0.0.1:18089` listener owner.
- Product conversation-store SHA-256 remained `fbae7e00b8f2275c90c6d769f27d3c1a458cc41528e59127d330d0c4630bcec7`.
- User Julia sessions SHA-256 remained `51702425a4a76f328490788c3890cc3bb2c05276fc57ff38532dbfb0a206fc43`.
- Julia requests from P1-B: 0.
- Julia state/process/config changes: none.
