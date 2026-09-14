# MIRA-E2E-P1-B — Golden Mira Isolated Runtime Composition

## Result

`PASS_READY_FOR_MIRA_E2E_P1_C_COMPATIBILITY_REBIND`

Rework review `5659417019` corrected model-visible user input binding. The public request no longer has an independent `task_intent`; exact `input_text` becomes `CurrentConversationalTaskContext.task_intent` before C03 sealing.

- Base: `08b8002b2973bf88dabe729d58e10d6ccab2968d`
- Composition entry point: `compose_golden_mira_runtime(...)`
- Runtime implementation: `julia_core/runtime/mira_composition.py`
- Tests: `tests/runtime/test_mira_composition.py`

## Composition

The isolated composition requires an absolute authority root, absolute conversation-store path, and an exact `MiraRuntimeShaPins` value. Core and Assistant pin mismatches fail before reconstruction. The runtime does not execute git; a launcher supplies expected and observed values.

The authority path is exactly:

`FilesystemDurableAuthorityReader` → `reconstruct_from_durable_authority` → exact repositories → `CanonicalSemanticAuthoritySource` → ordered `IdentityFrameSet` and `ExperienceFrameSet` → production C03 v3 `ExclusiveAdmissionGate` → `ExactAdmittedSemanticBinder` → `JuliaAssistantRuntime.prepare` → `ProviderExecutionEnvelope`.

Projected frames receive the canonical source-ref/source-digest binding required by the frozen C03 production gate. No canonical payload, digest, lifecycle, governance, or lineage value is rewritten.

The third admitted semantic unit is the serialized current-task context and retains provider roles `system/system/user`. Tests prove raw input appears verbatim as `task_intent`, `input_sha256` matches it, changing input changes both C03 gate receipt and final semantic fingerprint, and final message digest equals `semantic_fingerprint`. No prompt is appended after C03.

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

- Focused P1-B tests: 10 passed / 0 failed / 0 skipped / 0 warnings.
- Mandatory relevant regression: 267 passed / 0 failed / 0 skipped / 0 warnings, with one pre-existing ENG08 scope audit deselected because it does not recognize the separately authorized P1-B runtime path.
- Full candidate/reviewed-candidate audit: 267 versus 266 passes with the same single pre-existing scope-audit failure; the rework adds one passing focused test.
- `NO_CRITICAL_FALLBACK_GATE`: PASS, 0 new P0/P1 and one known nonfatal P2.
- `git diff --check`: PASS.
- Full `tests/runtime` audit at the original candidate had 17 pre-existing failures at both base and candidate, with 9 added P1-B tests; the rework adds one more focused proof without changing legacy runtime files.

## Julia Preservation

- PID 629 remained the `127.0.0.1:18089` listener owner.
- Product conversation-store SHA-256 remained `fbae7e00b8f2275c90c6d769f27d3c1a458cc41528e59127d330d0c4630bcec7`.
- User Julia sessions SHA-256 remained `51702425a4a76f328490788c3890cc3bb2c05276fc57ff38532dbfb0a206fc43`.
- Julia requests from P1-B: 0.
- Julia state/process/config changes: none.
