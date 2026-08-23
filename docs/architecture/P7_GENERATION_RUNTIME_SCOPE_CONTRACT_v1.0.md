# P7_GENERATION_RUNTIME_SCOPE_CONTRACT_v1.0

Status: SCOPE CONTRACT DRAFT (freeze pending review)
Date: 2026-08-23
Repository: `/Users/admin/julia_core`
Prerequisites:
- C-10 Gateway/Client Contract (FROZEN)
- B0_GATEWAY_BOUNDARY_EVIDENCE_REPORT_v1.0 (ACCEPTED)
- P7_GATEWAY_EVENT_CONVERGENCE_AUDIT (Architecture Gap CONFIRMED)

---

## 0. Why a Generation Runtime Is Needed

Current chain leaks Provider protocol to clients:

```text
Provider → OpenAI stream → Brain :18089 → SSE OpenAI format → Electron
                                                              → delta.content parsing
```

Electron understands `choices[0].delta.content` instead of Julia Core events.
The missing layer is the **Generation Runtime** — the Core semantic runtime
that translates Provider output into Core events.

Root cause:

```text
Missing Generation Runtime Semantic Layer
+ Provider Protocol Leakage
```

This is the same principle as Phase8:

```text
Provider Capability != Authority
```

## 1. Generation Runtime Definition

```text
Generation Runtime owns:
    generation_id
    sequence
    stream state
    cancel state
    provider adaptation

Generation Runtime must NOT own:
    identity meaning
    continuity mutation
    memory write
    persona evolution
```

Generation Runtime owns "how this generation runs", never "what this
generation means".

## 2. Generation Lifecycle State Machine

```text
                turn.accepted
                      |
                      v
             generation.started
                      |
        +-------------+-------------+
        |                           |
        v                           v
  assistant.streaming        cancelled
        |
        v
     assistant.completed
        |
        v
      canonical.commit
```

Critical: `assistant.completed` and `canonical.commit` MUST NOT be merged.

Possible: model generation completes → save fails → retry.
Possible: user barge-in → generation cancelled → turn still exists.

```text
Output completed != History established
```

## 3. Provider Adapter Boundary

Provider events are Transport-level. They must NOT become semantic events
directly:

```text
Provider finish_reason=stop  →  provider.finished ONLY
                             →  Core judges canonical completion
                             →  THEN assistant.completed
```

```text
Provider:  "I stopped emitting"
Core:      "Julia's expression is completed and part of history"
```

These are different. The adapter translates, never interprets.

## 4. Three-Tier Event Ownership

```text
A. Transport Event     (token chunk / stream closed / connection error)
   Owner: Provider / Transport Layer
   MUST NOT enter Julia semantic layer

B. Runtime Event       (generation.started / generation.cancelled /
                        generation.timeout)
   Owner: Julia Core Runtime (Generation Runtime)

C. Canonical Event     (turn.accepted / assistant.completed /
                        turn.committed)
   Owner: Julia Core Authority (Conversation + Context Core)
```

Forbidden mix:

```text
provider finish_reason=stop → assistant.completed   ✗
```

## 5. CoreEvent Source (frozen)

```text
OpenAI Provider
    ↓
Generation Runtime
    ↓
Core Event Translator
    ↓
Julia Core Event (CoreEvent)
```

Client receives CoreEvent, never ProviderEvent.

## 6. Electron Boundary

Electron remains a body:

```text
Electron KNOWS Julia Runtime Event schema
Electron must NOT judge: "this response became Julia history"
Electron only PRESENTS:  assistant.completed (with canonical_ref)
```

## 7. Voice / S2S Impact

Voice must share the same three IDs:

```text
conversation_id / turn_id / generation_id
```

Future audio streaming events:

```text
audio.started / audio.chunk / audio.completed
```

MUST inherit the same `generation_id`, otherwise text and audio diverge
(turn=10/generation=A vs audio_session=B) — breaks C-11.

## 8. Persona Host Boundary

```text
FORBIDDEN:  Persona Host → CoreEvent (capability carrier cannot emit
            identity events)
REQUIRED:   Persona Host → artifact metadata → Julia Core → semantic event
```

```text
✗ persona_loaded → Julia exists
✓ artifact.available → Core may bind runtime capability
```

## 9. AT-17 Regression Requirement

Generation Runtime is a capability layer. Standing gate:

```text
every generation-runtime commit → at17 regression gate
→ 14/14 attacks still REJECT
→ 14/14 invariants still PASS
→ zero semantic mutation
```

## 10. Acceptance Criteria

```text
[ ] Provider output reaches clients ONLY as CoreEvent (via Generation Runtime)
[ ] assistant.completed carries canonical_ref; client never infers completion
    from transport done
[ ] generation_id / sequence / stream / cancel state owned by Generation
    Runtime
[ ] Electron consumes CoreEvent schema (not OpenAI delta as semantic event)
[ ] Voice shares conversation_id / turn_id / generation_id
[ ] OpenAI-compatible endpoint preserved as compatibility surface
    (compatibility surface != canonical event surface)
[ ] AT-17 regression gate: 14/14 preserved
[ ] Zero identity / continuity / memory / persona mutation by Generation
    Runtime
```

## 11. Freeze Decision

```text
[ ] Generation Runtime definition approved
[ ] Generation lifecycle state machine approved
[ ] Provider adapter boundary approved
[ ] Three-tier event ownership approved
[ ] CoreEvent source approved
[ ] Electron boundary approved
[ ] Voice alignment approved
[ ] Persona Host boundary approved
[ ] AT-17 regression requirement approved
[ ] Acceptance criteria approved
```

Until this contract freezes, no Generation Runtime implementation code may be
written.

---

## Final Statement

Julia Core solved: "who has the right to define Julia?"

P7 solves: "who has the right to define that one Julia behavior has happened?"

Two different layers of a continuity system. Both must be frozen before
clients stop coupling to Provider transport. 🔒
