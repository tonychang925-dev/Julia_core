# Wave5 Authority Completion Phase — Route Record

Status: ACTIVE
Date: 2026-08-23
Repository: `/Users/admin/julia_core`
Branches: `cm-r0-fix` (base) / `wave5/authority-consolidation` (consolidation lane)

Source plan: `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`

---

## 1. Gate Status Update

| Gate | Prior | Now | Reason |
|---|---|---:|---|
| Pre-E2E Readiness | PASSED ✅ | PASSED (conditional) ✅ | Candidate lineage identified; AT-17~20 authority completion pending |
| E2E Execution | NEXT ▶ | DEFERRED ⏸️ | AT-17~20 authority completion + baseline regression closure pending |
| AT-03~09 lineage consolidation | — | NEXT ▶ | Frozen evidence lives on `at04` branch, not yet on `cm-r0-fix` |
| Baseline regression classification | — | NEXT ▶ | 44 failed / 3 errors must be closed by class before E2E |
| AT-17 | HOLD ⚠️ | QUEUED (after consolidation) | Claude migration / external continuity boundary |
| AT-11 remediation | HOLD | HOLD (unchanged) | S2S scope isolation stands; no premature remediation |

---

## 2. Rationale

AT-01~16 establish authority boundaries ("what is eligible to be truth"):

```text
AT-08 Pagination        → view mechanism ≠ history authority
AT-09 Derived indexes   → projection ≠ canonical history
AT-10 Electron cache    → client cache ≠ conversation authority
AT-12~16 Diary suite    → semantic authority separation
```

E2E with unresolved AT-17~20 gaps is a black-box: a failure cannot be attributed to
(a) boundary gap, (b) fixture/environment, or (c) integration wiring.

Therefore AT-01~20 are treated as one **authority contract suite**, and E2E is the final
**system composition proof** — run only after each boundary is individually proven.

### AT-20 definition (updated)

AT-20 is a **Recovery Authority Boundary Test**, not a full-stack E2E case:

```text
restart → state recovery → authority preserved
```

It answers: "after the system restarts, who decides who I am and what history I have?"
`continuity != runtime survival`. It stays in the AT layer, before E2E.

## 3. AT Boundary Contract

| AT | Boundary |
|---|---|
| AT-17 | Claude migration / external continuity boundary |
| AT-18 | Archive authority boundary |
| AT-19 | Hard-delete authority boundary |
| AT-20 | Full restart recovery authority boundary |

## 4. Execution Order

```text
1.  Wave5 Authority Consolidation Merge Audit
2.  AT-03~09 selective cherry-pick — Layer 1 (contract/evidence)
3.  Gateway production regression fix          ★ B0 priority
4.  Voice reconciliation contract cleanup       (B1)
5.  Context OS standalone regression cleanup    (B2)
6.  AT-03~09 IA dependency reconciliation       (Layer 2)
7.  AT-17 Audit
8.  AT-18 Audit
9.  AT-19 Audit
10. AT-20 Audit
11. Final E2E Readiness Re-check
12. E2E
```

E2E stays DEFERRED until step 11 passes. AT-11 remediation remains HOLD throughout.

## 5. Lineage Consolidation Decision

### Layer 1 — contract/evidence consolidation

Selective cherry-pick onto `cm-r0-fix`:

- 26 FROZEN evidence commits (AT-03~09 tests + freeze records)
- 5 SUPPORT source commits (minimal remediation required by the frozen tests)
- NOT picked: ~97 wave4-integration-base history commits (DIA / Wave1-3 / W2 / CORE-C1)

Minimal authority closure. No W2 architecture reconstruction is imported.

### Layer 2 — IA dependency reconciliation (separate audit)

Hard dependency: `julia_core/runtime/conversation_management_service.py` does not exist on
`cm-r0-fix`; 12 of 20 AT-03~09 tests (incl. all 9 IA) import it.

Decision principle:

```text
test dependency ≠ architecture authority
```

Layer 2 answers whether that module is (A) a still-required runtime component, or
(B) a legacy test dependency. The answer decides IA evidence landing — not the reverse.

## 6. Baseline Regression Classification

Baseline: `44 failed, 619 passed, 3 errors` (cm-r0-fix, 2026-08-23)

### Category A — environment / fixture (34)

| Cluster | Count | Root cause |
|---|---:|---|
| E2E HTTP | 9+3 | Brain `:18089` not running; proxy `127.0.0.1:7890`; missing fixtures `conv_id/turn_id/content` |
| `context_os` fixtures | 16 | `__new__` bypasses `__init__`; `_prepare_turn` now requires `context_os` |
| e3 architecture freeze | 5 | stale RTC contract tests; RTC moved to `voice_runtime/LiveKit` |
| MarketBrain | 1 | `ai_theme_app:8010` not running; asserts on live data |

Handling: E2E Environment Stabilization Report (why-fail / expected / owner).

### Category B — real regression (13)

| Cluster | Count | Severity | Root cause |
|---|---:|---:|---|
| Gateway | 8 | **B0** | `C1.2/C1.3a` moved `current_topic/turn_count` into `TurnContext`; production `gateway_server.py` still reads `JuliaSession` attrs → `/chat` + voice turns crash |
| Voice reconciliation | 4 | B1 | modality projection dropped; interrupted assistant filtered by `status==completed`; identity token detection only Chinese — continuity/identity contract gap (not S2S transport) |
| Context OS a21 | 1 | B2 | `context_os/providers/market_context.py` contains `market/theme/ai_theme_app` terms (real code, not comments) |

### B0 rationale

Gateway is the shared entry of `/chat` + voice turn path. If broken: Text, Voice,
Assistant runtime all affected. This is a **Frozen Contract Regression**:
`AT-03/04 FROZEN PASS` yet production path BROKEN → frozen ≠ stable.

## 7. Freeze Decision

No freeze rows are marked locked in `wave5-acceptance.md` until:

```text
[ ] AT-03~09 lineage consolidated onto cm-r0-fix
[ ] B0 gateway regression closed
[ ] B1 voice contract cleanup closed
[ ] B2 context_os contamination closed
[ ] Category A environment items recorded with owners
[ ] AT-17~20 audits PASS
[ ] Final E2E Readiness Re-check PASS
```

E2E remains DEFERRED until the above holds. 🔒
