# CLN-06 — Trigger Boundary Verification

**Status:** VERIFICATION (no code change)
**Date:** 2026-08-19
**Scope:** CONT-DIA-3 (Core reflection trigger semantics) vs STORAGE-DIA-3 (product trigger runtime)

---

## Verdict: ✅ GREEN — no RED, no duplicate implementation

The trigger boundary is already correctly layered. No production code change is required.

---

## 1. CONT-DIA-3 Core owns (verified)

`julia_core/reflection_trigger/models.py` is the sole authority for:

| Concern | Canonical surface |
|---|---|
| Opportunity identity | `OpportunityKey` + `opportunity_id` property (models.py:266, 305) |
| Pending opportunity semantics | `PendingOpportunity` |
| Trigger admission state | `EventEligibilityBoundary`, `DeterministicTimerEligibilityBoundary` |
| Causal identity | `SingleEventAnchor`, `ActivityWindowAnchor`, `QuietWindowAnchor` |
| Trigger reason/source | `TriggerKind`, `TriggerSourceRef`, `TriggerReason` |

---

## 2. RED signals checked — all clean

| Signal | Result |
|---|---|
| Product layer generates its own `opportunity_id` | ✅ clean — `def opportunity_id` exists only at `reflection_trigger/models.py:305` |
| Product layer redefines `ReflectionOpportunity`/`PendingOpportunity` | ✅ clean — referenced only by `reflection_context` (CONT-DIA-4, legitimate Core-internal dependency) |
| Product layer redefines trigger admission/causal identity | ✅ clean — no product module defines admission boundaries or anchors |

---

## 3. Product-layer protocol (STORAGE-DIA-3) — correctly scoped

`docs/authority/W3_A1_REFLECTION_TRIGGER_PROTOCOL.md` (FROZEN) defines only:

- trigger **source classification** (conversation close, relationship event, …)
- trigger **outcome** `{REFLECT, SKIP}`
- invariant "trigger = opportunity, never command"

It does **not** redefine opportunity identity, admission, or causal identity. The product trigger runtime (`STORAGE-DIA-3`) is not yet implemented — its sabotage suite is still `SPEC`, not `PASS`.

---

## 4. Frozen boundary (unchanged)

```
CONT-DIA-3 owns (frozen):
  ReflectionOpportunity identity
  PendingOpportunity semantics
  canonical trigger admission state
  causal identity / trigger truth

STORAGE-DIA-3 may only:
  timer / event / manual signal → adapter → CONT-DIA-3 canonical objects

STORAGE-DIA-3 must NOT:
  reimplement opportunity identity / admission / causal identity / trigger truth
```

---

## 5. Conclusion

Trigger boundary verification passes with **zero RED**. The `W3_A1` protocol is product-scoped (source classification + outcome semantics) and does not leak into CONT-DIA-3's frozen Core concerns. No code change, no rewrite-as-adapter, no retire.
