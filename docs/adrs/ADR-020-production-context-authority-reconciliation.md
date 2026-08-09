# ADR-020 — Production Context & Conversation Authority Reconciliation

**Status**: ACCEPTED 2026-08-09
**Supersedes**: None (new)
**Scope**: julia_core architecture freeze — READ-ONLY, no code changes

## Context

A CORE-C0.1 audit of the production conversation path revealed that `JuliaSession._prepare_turn()` assembles model-facing context by direct string concatenation of six context sources (identity, experiences, market evidence, capability manifest, interaction state, conversation state + `history[-20:]`), bypassing the Context OS pipeline defined in JULIA_CORE_PRINCIPLES.md and CONTEXT_OS_DESIGN.md.

Simultaneously, `ConversationRuntime` now correctly owns canonical transcript authority (CORE-C1 series), but Continuity OS, Memory OS, and Context OS are not yet integrated into the production cognitive pipeline.

## Decision

Ten authority boundaries are frozen:

1. **ConversationRuntime is canonical transcript authority.**
   Owns complete message history, turn ordering, message identity, modality, status. All turn paths (text, voice, streaming, external import) route through it.

2. **Context OS is sole model-visible context authority.**
   All information reaching the model MUST pass through Context OS. `_prepare_turn()` is transitional and must eventually delegate to Context OS. No domain, provider, or application surface may assemble model context independently.

3. **`JuliaSession._prepare_turn()` is TRANSITIONAL.**
   It is not a second Context OS. It must be migrated to ContextExecutionRuntime (CXT-C3).

4. **Raw canonical transcript is not Memory.**
   Conversation messages are durable facts. Memory OS decides which experiences warrant governed long-term persistence. Raw transcript is input to Memory governance, not its output.

5. **Raw transcript is not ContinuityCheckpoint.**
   Checkpoints store identity anchors, protected memory refs, and recovery plans — not full conversation history.

6. **Continuity OS governs preservation/recovery policy, not raw history persistence.**
   It answers "what must survive and why" — not "where is the chat log."

7. **Context reconstruction ≠ old context-window restoration.**
   Recovery produces a ContextReconstructionRequest → new ContextBlocks, not reloading a previous prompt.

8. **Electron/Voice may transport Core-issued context, but may not select cognitive history independently.**
   Voice bootstrap (last 10 turns) is C1B compatibility only. Final path: Core Context OS → ContextPackage → S2S.

9. **SessionStore Wake State is legacy compatibility behavior.**
   `_load_recent_experiences()` reading `~/.julia/sessions.json` is not canonical continuity authority. It will be retired when Context OS reconstruction replaces it.

10. **`history[-20:]` is transitional compatibility behavior.**
    The hardcoded window will be replaced by Context OS transcript lifecycle (ActiveTail, StructuredCompact, ContextBoundary).

## Consequences

- `_prepare_turn()` continues to operate in production but is formally marked transitional.
- CXT-C1 defines the canonical transcript lifecycle contract.
- CXT-C2 formalizes migration from legacy transcript stores.
- CXT-C3 binds Context OS to the production cognitive pipeline.
- CXT-C4 integrates Continuity OS checkpoint/recovery with the runtime.
- Codex/Electron must not implement cognitive history selection.
- Voice bootstrap (last-10-turn seed) is frozen as C1B compatibility bridge — not as permanent Context OS path.
