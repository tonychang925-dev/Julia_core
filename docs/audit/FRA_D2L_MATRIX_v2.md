# FRA-D2-L v2 — C-00~C-12 LOCAL/STATIC COMPLIANCE (MIRA REVALIDATED)
**Date: 2026-08-11 | Mode: READ ONLY | Replaces: D2-L v1**

---

## C-00 — Cognitive Boundary
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     PARTIAL / KNOWN VIOLATION
  VIOLATION: WorkflowRouter / requires_tool performs pre-cognitive
             semantic capability-need classification (keyword matching)
  VIOLATION: RuntimeCapabilityBridge retains intent-based resolution
  OK:         LLM cognition called through JuliaSession provider
SOURCE:           julia_session.py:105 (WorkflowRouter), :308 (requires_tool)
```

## C-01 — Runtime Execution
```
SEMANTICS:          AMEND CANDIDATE
IMPLEMENTATION:     KNOWN FAIL
  FAIL:      cancel_streaming_turn:326 marks user=failed (violates CM-I05)
  CONFIRMED: C-C007 LIVE in Brain import
SOURCE:           conversation_runtime.py:326
```

## C-02 — Conversation Authority
```
SEMANTICS:          SUPERSEDE-v2 CANDIDATE
IMPLEMENTATION:     PARTIAL / NORMATIVE CONFLICT
  CONFLICT:  C-C001: R1-B immediate-completed vs C-02 v1 pending→completed
  AMBIGUITY: C-C002: VoiceWorkspace holds completed turns (timing TBD)
  AMBIGUITY: C-C003: flush/commitExternalTurns path (timing TBD)
SOURCE:           conversation_runtime.py, voice-workspace.js (Golden)
```

## C-03 — Context OS
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     PARTIAL / KNOWN VIOLATIONS
  VIOLATION: ActiveTail still has 40-msg hard cap (len(tail) > max_turns*2)
  VIOLATION: post-Context model-visible message injection exists
             (messages.append/insert in _chat_impl after ContextPackage)
  OK:        get_canonical_history removes old get_history(40) cap
  OK:        CognitiveContextPackage structure exists
SOURCE:           context_execution_runtime.py:235-236, julia_session.py:313-336
```

## C-04 — Identity/Persona
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     PARTIAL
  GAP:       IdentityFrame sourced from persona:feature_store (get_traits_for_injection)
             Not yet bound to canonical IdentityContract per C-04 design
SOURCE:           context_execution_runtime.py:130-133
```

## C-05 — Memory OS
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     PARTIAL
  GAP:       ExperienceFrame uses legacy SessionStore Wake State
             (_load_recent_experiences → session_store:wake_state)
             Not yet using governed MemoryExperience retrieval
SOURCE:           context_execution_runtime.py:148-153
```

## C-06 — Continuity OS
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     NOT PRODUCTION-BOUND
  STATUS:    ContinuityFrame explicitly reserved for P5
             "Reserved for P5 Continuity binding"
SOURCE:           context_execution_runtime.py:190
```

## C-07 — ModelProvider
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     PARTIAL
  OK:        ModelProvider abstraction exists (JuliaSession → provider.chat)
  GAP:       Governed C-03→C-09→C-07 input pipeline incomplete
             (C-03 has bypasses, C-09 not bound)
SOURCE:           julia_session.py:202,305
```

## C-08 — Capability/Tool
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     PARTIAL / KNOWN VIOLATION
  VIOLATION: requires_tool() performs semantic keyword classification
  VIOLATION: intent-based capability resolution remains (resolve_market_intent)
  VIOLATION: Backward-compat path production-reachable
  OK:        CapabilityManager exists, tool-call execution path exists
SOURCE:           julia_session.py:308, runtime/capability/
```

## C-09 — Alignment
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     TRANSITIONAL / NOT PRODUCTION-BOUND
  STATUS:    to_messages() explicitly "Transitional — replaced by Alignment
             projection (C-09) in P6"
             Current production path: ContextPackage → to_messages → provider
SOURCE:           context_execution_runtime.py:42-43
```

## C-10 — Gateway/Client
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     PARTIAL
  OK:        Electron conversation-store self-declared disposable
  GAP:       Core-first create local-only, not deployed
  GAP:       Voice→Text protocol mismatch in source (live-message vs transcript)
  UNAUTH:    app.js +17 lines (voiceSyncTimer)
SOURCE:           julia_electron_v2/src/
```

## C-11 — Voice/Media
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     PARTIAL
  GAP:       Golden source contains voice_bootstrap / workspace paths
  OK:        Brain ignores external_history (native_stream path)
  OK:        ASR final → Brain → Core path exists
  UNKNOWN:   Current AutoDL live deployment
SOURCE:           Julia-Voice-S2S/frontend/, openai_compat.py
```

## C-12 — Evidence/Action/Trace
```
SEMANTICS:          RETAIN CANDIDATE
IMPLEMENTATION:     PARTIAL / NOT FULLY VERIFIED
  OK:        Event store, trace modules exist
  GAP:       Complete contract binding not demonstrated
SOURCE:           julia_core/events/, julia_core/evidence/
```

---

## CORRECTED GLOBAL SUMMARY

```
KNOWN FAIL (source):              C-01 (cancel_streaming_turn)
PARTIAL / KNOWN VIOLATION:        C-00, C-03, C-08
PARTIAL / TRANSITIONAL:           C-02, C-04, C-05, C-07, C-09, C-10, C-11, C-12
NOT PRODUCTION-BOUND:             C-06

ZERO contracts fully COMPLIANT
```

### ROOT FINDING
The C-series contracts were FROZEN at the architecture level, but
implementation was mid-migration (P2-P6 transitional state).
"Contract FROZEN" was conflated with "Contract IMPLEMENTED."
The 27/27 E2E further misrepresented partial Core migration as
production architecture complete.

