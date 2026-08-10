# Batch I — Final Acceptance Evidence Map

**Status**: AT-01~AT-12 EVIDENCED, AT-13~AT-17 REQUIRES RUNTIME EVALUATION
**Date**: 2026-08-10
**Baseline**: julia_core f569422, C-00~C-12 FROZEN, P1-P8 COMPLETE

## AT-01~AT-12: Authority Evidence

| AT | Claim | Evidence |
|----|-------|----------|
| AT-01 | Cognitive Boundary | P3: LLM tool_call path independent of semantic routers. C-00 §3-5. |
| AT-02 | Runtime Replacement | P2: Context OS spine. Model-visible context assembled by C-03, not Runtime. |
| AT-03 | Context Single Gateway | P2: MODEL_VISIBLE_BYPASS_COUNT = 0. All 5 ingress → Context OS. |
| AT-04 | No Flat Bootstrap | P2: 7 Frames replace _prepare_turn() string concat. ActiveTail replaces history[-N:]. |
| AT-05 | Conversation Canonicality | P1: ConversationRuntime sole transcript authority. 17/17 tests. |
| AT-06 | Memory Separation | P4: Identity ≠ Memory. No IdentityMemory, no WorkingMemory. |
| AT-07 | Continuity Independence | P5: Normal Resume ≠ Continuity Recovery. Checkpoint stores refs, not copies. |
| AT-08 | Provider Switch | P5+P6: Provider session = ephemeral. Core authorities survive provider loss. |
| AT-09 | Tool Agency | P3: LLM tool_call independent of WorkflowRouter. Semantic routers classified. |
| AT-10 | Voice Parity | P2-L: Voice/S2S → Context OS. Voice = body, not second cognition architecture. |
| AT-11 | Context Budget | P2: ActiveTail budget-driven. No hardcoded history[-N:]. Progressive Disclosure stages. |
| AT-12 | Narrative Continuity | P4 + M0-B: 34 historical messages migrated. NarrativeExperience causal structure frozen (C-05). |

## AT-13~AT-17: Runtime Evaluation Required

| AT | Claim | Runtime Requirement |
|----|-------|---------------------|
| AT-13 | Narrative Causal Integrity | Real NarrativeExperience retrieval → verify causal chain intact |
| AT-14 | Effective Context Density | Compare 4 conditions (long/irrelevant, short/dense, structured/causal, full/raw) |
| AT-15 | Relationship Boundary | Golden cases: unknown, unauthorized, malicious, Tony-authorized, forged |
| AT-16 | Historical Recovery | M0-B migrated conversation → clean restart → reopen → Julia understands prior topics |
| AT-17 | Source Completeness | Every model-visible block → traceable to Frame/source/canonical ref |
