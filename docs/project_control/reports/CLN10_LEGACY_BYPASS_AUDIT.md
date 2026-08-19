# CLN-10 — Legacy / Bypass Audit

**Status:** AUDIT (no code change)
**Date:** 2026-08-19
**Scope:** legacy / fallback / bypass surfaces that could sidestep Core authority

---

## Verdict: ✅ GREEN — zero RED-BYPASS

All six RED-LB signals are clean. Prior hardening (CM-FAILCLOSED, FC-AUDIT, CM-R1) already closed the bypasses. No repair required.

---

## 1. RED-LB signals — all clean

| Signal | Result | Evidence |
|---|---|---|
| RED-LB1 legacy transcript/store writes canonical truth | ✅ clean | `LegacyJsonConversationRepository` has `set_read_only()`; `SessionRepository` raises `RepositoryReadOnlyError("repository retired; read-only")` on write (repository.py:79-98) |
| RED-LB2 persona/diary/legacy memory bypasses Context OS | ✅ clean | `release_gate.py:110` `forbidden_state` includes `persona_prompt`/`memory_dump`/`raw_conversation`; `provider_adapter.py` tracks `contains_persona_prompt=False` |
| RED-LB3 product/runtime bypasses Core trigger/continuity/diary ports | ✅ clean | verified in CLN-06 (trigger) + CLN-07 (diary) — no product-layer reimplementation |
| RED-LB4 cache/index/derived becomes recovery authority | ✅ clean | `context_execution_runtime.py` "All Frames are derived, never canonical"; interaction cache "rebuild from canonical message history" (conversation_runtime.py:326); catalog updated AFTER canonical append |
| RED-LB5 get_or_create / fallback auto-creates canonical state | ✅ clean | `get_or_create(create=False)` default; raises `ValueError` on absent (conversation_runtime.py:312-320, "CM-FAILCLOSED F4") |
| RED-LB6 deprecated writer reachable from production path | ✅ clean | legacy repository retired read-only; `SessionStore.messages[]` shadow transcript retired (session_store.py:65, "CM-R1") |

---

## 2. Classification (no RED-BYPASS)

| Surface | Classification |
|---|---|
| `LegacyJsonConversationRepository` | `READ-ONLY` (retire mechanism) |
| `SessionStore` shadow transcript (`messages[]`) | `DEAD/UNREACHABLE` (retired, derived catalog only) |
| `memory_store._from_legacy_item` (legacy JSONL) | `MIGRATION-ONLY` (legacy → MemoryObject) |
| interaction cache / derived catalog / Frames | `DERIVED-CACHE` (rebuild from canonical) |
| `get_or_create` | hardened (fail-closed, not a bypass) |

---

## 3. Reused evidence (no re-fix)

- CM-FAILCLOSED F4 — fail-closed on resume/bind/turn auto-create
- FC-AUDIT — `gateway.get_or_create` hardened
- CM-R1 — `SessionStore` shadow transcript retired
- CM-FAILCLOSED-01 — silent fallback eradication

These prior fixes are already present in the merged tree; CLN-10 confirmed their persistence, no re-implementation.

---

## 4. Conclusion

Legacy/bypass audit passes with **zero RED-BYPASS**. The only `RED-*`-eligible surfaces are either already `READ-ONLY`, `DEAD`, `MIGRATION-ONLY`, or `DERIVED-CACHE`. No deprecated writer remains reachable from the production path, and no derived state can become canonical recovery authority.
