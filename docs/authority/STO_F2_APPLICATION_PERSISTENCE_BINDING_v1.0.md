# STO-F2 Application Persistence Binding v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: STO-F2 — Application Persistence Binding (Wave 0)
BASE: cm-r0-fix @ `f545d9c` (canonical); STO-D0 frozen @ `261521f`; STO-F1 frozen @ `23ecc1f`

## Governing principle

```text
Physical host ≠ semantic owner.

Core decides WHAT is true.
Assistant proves THAT truth was physically persisted.
```

## Scope

F2 does NOT decide Conversation JSONL (CM-S1), Diary entry format (DIA), or Backup algorithm (OPS). It answers only: who may take the resolved root, and how Core's semantic ports bind to Assistant-owned physical adapters.

## The only legal wiring

```text
            Julia Core (semantic authority)
                   │
             abstract ports
                   │
                   ▼
        Julia-AI-Assistant
        ApplicationCompositionRoot
                   │
          ┌────────┼─────────┐
          ▼        ▼         ▼
     Conversation  Diary   Memory/…
       Adapter    Adapter  Adapter
          \        |        /
           \       |       /
            ▼      ▼      ▼
        ResolvedPrivateDataRoot
                   │
                   ▼
          <PRIVATE_JULIA_DATA>
```

## 1. Single composition root

ADR-033's frozen ownership is made executable:

```text
Julia-AI-Assistant = sole application composition root
                     for canonical persistence bindings
```

Forbidden:

```text
Core → pathlib/open(private root)      ❌
Electron → memory/conversations/…      ❌
S2S → memory/conversations/…           ❌
Brain handler → directly edit transcript ❌
```

Correct:

```text
Core semantic service → Port → Assistant adapter → filesystem
```

## 2. Path opacity

Wrong:

```text
ConversationRuntime(private_data_root="/Users/...")
```
(once Core receives a physical root, someone will soon `os.path.join` it — boundary dies)

Correct:

```text
ConversationRuntime(conversation_repository=...)
```

Core sees `ConversationRepositoryPort` / `DiaryRepositoryPort` / `MemoryRepositoryPort` — never `PRIVATE_JULIA_DATA_ROOT`, `Path`, or filesystem layout. F1 resolver output stays inside the Assistant composition layer and never penetrates Core's semantic runtime.

## 3. Least-authority namespace binding

Not "ConversationAdapter receives the whole `/JuliaAI` root and may touch diary/backups/identity". The composition root hands out per-namespace capabilities:

```text
ApplicationCompositionRoot
  ├── conversation namespace capability
  ├── diary namespace capability
  ├── memory namespace capability
  ├── continuity namespace capability
  ├── backup namespace capability
  └── index namespace capability
```

Conversation adapter receives `<root>/memory/conversations/` as a constrained capability — not an unrestricted-root master key.

## 4. Single layout derivation

Forbidden: every module hardcodes `root / "memory" / "conversations"`. Exactly one `PrivateDataLayout` (defined by Assistant) derives all namespaces:

```text
PrivateDataLayout {
    conversations, diary, experiences, identity, continuity,
    runtime, indexes, backups, migrations, logs
}
```

```text
ResolvedPrivateDataRoot → PrivateDataLayout → adapters (take layout capabilities)
```

Future layout migration never triggers a dozen modules each guessing paths.

## 5. Port semantics vs adapter physics

```text
Core owns:
  append accepted ConversationMessage
  read canonical messages
  lookup by turn/message identity
  conversation lifecycle semantics
  ordering/idempotency expectations

Assistant adapter owns:
  open() / write_all() / flush() / fsync() / directory fsync
  file permissions / segment path / filesystem errors
```

Core may require "this append must be durable"; Core must NOT write `os.fsync(fd)`.

```text
Core specifies semantic outcome. Adapter proves physical outcome.
```

## 6. No semantic mutation by adapter

Given `ConversationMessage(id, role, content, turn_id)`, the adapter MUST NOT:

```text
modify content / reassign message_id / change role / reorder / merge two messages / silently filter one
```

```text
Adapter may encode; adapter may not reinterpret.
```

The Diary adapter cannot decide "this passage is touching, I'll keep it for Julia" — that is Diary governance's authority.

## 7. Startup ordering

```text
Assistant starts
  → F1 ResolvePrivateDataRoot → ROOT_READY
  → construct PrivateDataLayout
  → construct physical adapters
  → validate required bindings
  → inject ports into Julia Core
  → Core runtime accepts canonical work
```

Forbidden: Core accepts a user turn while a resolver later initializes storage. The Conversation canonical path must have `required persistence binding READY` before canonical acceptance is enabled.

## 8. Required vs optional bindings

```text
REQUIRED FOR CONVERSATION AUTHORITY:
  ConversationRepository, ConversationLifecycleStore (or equivalent)
  → unbound = canonical conversation acceptance unavailable

OPTIONAL / FEATURE-SCOPED:
  DiaryRepository  → Diary feature unavailable (never Conversation rollback)
  FTS              → Search unavailable (Conversation continues)
  Backup worker    → backup degraded (canonical append continues)
```

Inherits `DIARY_DURABLE ≠ CORE_ACCEPTED`.

## 9. No shadow fallback

Required canonical adapter fails at startup → the most dangerous response is "use an in-memory repository for now" (Julia seems to chat, everything vanishes on restart).

```text
required canonical adapter unavailable → feature FAIL CLOSED
```

Tests may inject fake/in-memory adapters; production canonical path must never silently fall back.

## 10. Binding identity provable (PersistenceBindingReport)

After composition, produce a runtime-visible, non-semantic:

```text
PersistenceBindingReport {
    root_id: <storage_root_id>
    layout_version: 1
    bindings:
      conversation: {adapter: SegmentedJsonlConversationRepository, status: READY}
      diary:        {adapter: MarkdownDiaryRepository, status: NOT_IMPLEMENTED}
      search:       {adapter: SQLiteConversationSearchIndex, status: NOT_IMPLEMENTED}
}
```

```text
report = observability/provenance ≠ authority (cannot change Core semantic state)
```

## 11. Binding epoch stability

Resolved root + canonical bindings are immutable for a runtime binding epoch. Environment/path changes MUST NOT silently redirect live canonical persistence (`turn 1 → A`, `turn 2 → B`). Changing root requires explicit shutdown/migration/cutover (ADR-002 family).

## 12. Governed adapter cutover

Replacing a canonical adapter (e.g. `LegacyRepository → SegmentedJsonlRepository`) is an authority cutover, not ordinary DI:

```text
FREEZE → RECONCILE → VERIFY → ACTIVATE → RETIRE
```

F2 need not define the full migration algorithm, but MUST freeze: canonical repository binding replacement = authority cutover.

## 13. Error boundary

Physical errors (EIO / ENOSPC / permission denied / fsync failure / marker/root drift) are translated into structured persistence failures — never raw `OSError` leaking as "LLM failed":

```text
PERSISTENCE_BINDING_UNAVAILABLE
PERSISTENCE_WRITE_FAILURE
PERSISTENCE_DURABILITY_FAILURE
PERSISTENCE_CONFLICT
PERSISTENCE_CORRUPTION_DETECTED
PERSISTENCE_NAMESPACE_VIOLATION
PERSISTENCE_CUTOVER_REQUIRED
```

D0-03's `STORAGE_DURABILITY_FAILURE` remains a valid lower-layer/concrete error; F2 does not rename it.

## 14. Brain handler cannot bypass Core

```text
HTTP Brain → Core semantic API / ConversationRuntime → Repository Port → Assistant Adapter
```

Never `conversation_adapter.append(...)` bypassing `ConversationRuntime`. Physical ownership does not imply semantic write authority.

## S1 — Boundary-scoped path opacity (normative)

Raw canonical filesystem paths MUST NOT cross the physical→semantic boundary through:

```text
Core-facing exceptions
semantic/structured persistence errors
PersistenceBindingReport
cross-boundary logs/events/observability
```

Otherwise Core, without receiving a path directly, re-learns physical layout from a leaked `PermissionError("/Users/.../memory/conversations/...")` — making F2-I02 formal only.

Assistant-local secure diagnostics MAY retain physical paths (the physical host must troubleshoot); the prohibition is boundary-scoped, not "path strings may never exist anywhere".

## S2 — Namespace capability is an operation capability (normative)

Least-authority namespace ≠ handing the adapter a shorter raw `Path`:

```text
ConversationAdapter(root=Path("/.../memory/conversations"))
→ root.parent.parent / "diary"   # escapes in one step
```

Correct concept:

```text
ConversationStorageCapability
  allowed:
    open/create canonical conversation segment
    list owned conversation artifacts
    fsync owned files/directories
    delete owned artifact under governed operation
  not exposed:
    parent / raw private root / arbitrary sibling traversal
```

```text
least authority = constrained operation surface, not a shorter path string
```

## Invariants

**F2-I01 — Single Composition Root**

```text
Julia-AI-Assistant MUST be the sole application composition root for
canonical persistence adapters.
```

**F2-I02 — Core Path Opacity**

```text
Julia Core MUST NOT receive, resolve, derive, or directly use
PRIVATE_JULIA_DATA_ROOT or filesystem paths for application persistence.
```

**F2-I03 — Port/Adapter Boundary**

```text
Core owns persistence semantics through ports.
Assistant adapters own physical persistence mechanics.

Neither side may silently assume the other's authority.
```

**F2-I04 — Least-Authority Namespace Binding**

```text
Each physical persistence adapter MUST receive only the filesystem
namespace/capability required for its responsibility, not unrestricted
private-root authority by default.
```

**F2-I05 — Single Layout Derivation**

```text
Application persistence namespaces MUST be derived centrally from one
ResolvedPrivateDataRoot / PrivateDataLayout.

Independent hard-coded canonical paths are forbidden.
```

**F2-I06 — No Semantic Mutation by Adapter**

```text
Physical adapters MUST NOT reinterpret, synthesize, reorder, or silently
mutate semantic canonical objects supplied by Core.
```

**F2-I07 — Required Binding Before Acceptance**

```text
Required canonical Conversation persistence bindings MUST be READY before
canonical user-turn acceptance is enabled.
```

**F2-I08 — Failure Isolation**

```text
Failure of Diary, Search, Backup, or other non-required feature-scoped
bindings MUST NOT roll back or replace already durable Conversation authority.
```

**F2-I09 — No Shadow Fallback**

```text
Failure of a required production persistence binding MUST NOT silently fall
back to in-memory, repo-local, legacy, or alternate persistence.
```

**F2-I10 — Binding Epoch Stability**

```text
The resolved root and canonical persistence bindings MUST remain stable for
a runtime binding epoch.

Environment/path changes MUST NOT silently redirect live canonical persistence.
```

**F2-I11 — Governed Adapter Cutover**

```text
Replacing an active canonical persistence adapter is an authority cutover and
MUST require explicit reconciliation and verification before activation.
```

**F2-I12 — Physical Host ≠ Semantic Authority**

```text
Assistant ownership of physical persistence MUST NOT grant Brain handlers or
adapters independent authority to create, accept, mutate, reorder, or delete
Core semantic truth.
```

## Sabotage suite (AT-BIND-01…20)

```text
AT-BIND-01  Core receives raw PRIVATE_JULIA_DATA_ROOT → contract violation          ✅
AT-BIND-02  Assistant resolves F1 root → one PrivateDataLayout → all adapters derive from it ✅
AT-BIND-03  Conversation adapter accesses diary namespace → namespace violation      ✅
AT-BIND-04  Electron directly opens canonical conversation files → forbidden        ✅
AT-BIND-05  S2S directly writes canonical ConversationMessage → forbidden            ✅
AT-BIND-06  Brain HTTP handler writes repository without ConversationRuntime → forbidden ✅
AT-BIND-07  required ConversationRepository missing at startup → canonical acceptance disabled ✅
AT-BIND-08  required repository init fails → no in-memory fallback                  ✅
AT-BIND-09  Diary binding unavailable → Conversation canonical path remains available ✅
AT-BIND-10  FTS binding unavailable/corrupt → Conversation canonical path remains available ✅
AT-BIND-11  Backup binding unavailable → Conversation canonical path remains available ✅
AT-BIND-12  adapter attempts to alter message_id/content/role → rejected/detected   ✅
AT-BIND-13  process environment root changes after binding → active root unchanged  ✅
AT-BIND-14  second resolver result points to another root mid-runtime → no silent rebind ✅
AT-BIND-15  legacy repository exists → cannot auto-become fallback authority        ✅
AT-BIND-16  active repository adapter replacement attempted directly → CUTOVER_REQUIRED ✅
AT-BIND-17  governed FREEZE→RECONCILE→VERIFY→ACTIVATE sequence → replacement may activate ✅
AT-BIND-18  adapter raises raw filesystem durability failure → structured persistence failure reaches semantic boundary, no fake acceptance ✅
AT-BIND-19  PersistenceBindingReport generated → accurate root_id/bindings → cannot mutate semantic state ✅
AT-BIND-20  same Core contracts run against different valid physical adapter → semantic behavior contract-equivalent ✅
```

## Freeze matrix

| Item | Decision |
|---|---|
| Composition root | Julia-AI-Assistant |
| Core receives root path | ❌ |
| Core owns semantic ports | ✅ |
| Assistant owns physical adapters | ✅ |
| Brain handler direct repository write | ❌ |
| Electron canonical FS access | ❌ |
| S2S canonical FS access | ❌ |
| Central PrivateDataLayout | ✅ |
| adapter gets whole root by default | ❌ |
| least-authority namespace | ✅ |
| required Conversation binding before acceptance | ✅ |
| silent in-memory fallback | ❌ |
| Diary failure blocks Conversation | ❌ |
| Search failure blocks Conversation | ❌ |
| Backup failure blocks Conversation | ❌ |
| root hot-switch | ❌ |
| adapter hot-switch | ❌ |
| governed cutover | ✅ |
| binding observability report | ✅ |
| report = semantic authority | ❌ |

## Document status vocabulary

- FROZEN: contract accepted and sealed (current).
