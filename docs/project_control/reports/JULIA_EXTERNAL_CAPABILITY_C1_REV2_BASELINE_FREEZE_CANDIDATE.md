# Julia External Capability Invocation — C1 REV2 Baseline Freeze Candidate

**Generated at:** 2026-08-26 14:30 Asia/Shanghai  
**Track:** Codex-A / Julia Core — External Capability Invocation  
**Phase:** C1-FINAL — REV2 Baseline Audit & Freeze Candidate  
**Scope:** tests / audit / docs only  
**Production mutation:** 0  

## 1. Authority Chain

This C1 baseline is subordinate to:

1. `JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0`
2. Frozen C-series contracts, especially `C-00`, `C-03`, `C-08`, `C-12`
3. `JULIA_EXTERNAL_CAPABILITY_INVOCATION_REFACTOR_DESIGN_REV2_FREEZE.md`

REV2 is a **feature-level implementation freeze**, not a Julia Core canonical architecture amendment.

## 2. Baseline HEAD

Tested C1 baseline HEAD before this report commit:

```text
00f45a9dbc13ca111b5944171daa46df095ad808
```

Reclassification patch included:

```text
00f45a9 test: reclassify unknown provider reachability as pending
```

Reason:

- R2.6 provider-source / provider-protocol xfail represented UNKNOWN source facts.
- Per C1-R2.9 rule: `UNKNOWN FACT != XFAIL IMPLEMENTATION GAP`.
- D-01/D-03 were reclassified from strict xfail to PENDING / pytest skip.

## 3. Branch-History Purity Evidence

Branch:

```text
feature/julia-external-capability-c1-rev2-contract-tests
```

Base:

```text
698b811dfb9c7aae3529ba354cb6baa20b65e9b6
```

C1 branch commits since base:

```text
52e902d docs: establish external capability C1 REV2 baseline
3b3f4e9 test: add C1 REV2 capability object contracts
1102fb4 test: add C1 REV2 cognitive boundary contracts
53fbc70 test: add C1 REV2 Context OS projection contracts
e70194b test: add C1 REV2 local provider release gate contracts
f03a9e0 test: add C1 REV2 authorization result semantics contracts
7c845da test: add C1 REV2 sync stream authority parity contracts
367948e test: add C1 REV2 ai_theme degradation contracts
fa816df test: add C1 REV2 action trace semantics contracts
09fac33 test: add C1 REV2 legacy reachability gates
00f45a9 test: reclassify unknown provider reachability as pending
```

Files changed since base before this report:

```text
docs/project_control/JULIA_EXTERNAL_CAPABILITY_C1_REV2_BASELINE_EVIDENCE.md
tests/capability/test_c1_rev2_ai_theme_degradation.py
tests/capability/test_c1_rev2_authorization_and_result_semantics.py
tests/capability/test_c1_rev2_contract_objects.py
tests/capability/test_c1_rev2_filesystem_security.py
tests/capability/test_c1_rev2_provider_resolution.py
tests/runtime/test_c1_rev2_action_trace_semantics.py
tests/runtime/test_c1_rev2_cognitive_boundary.py
tests/runtime/test_c1_rev2_context_os_projection.py
tests/runtime/test_c1_rev2_legacy_reachability_contract.py
tests/runtime/test_c1_rev2_sync_stream_authority.py
```

Conclusion:

```text
Production files in C1 branch history: 0
REV1 C1 test files present: 0
773feb5 extended: NO
```

## 4. Complete Baseline Matrix

| Working phase | Test file | Protected contract | Canonical design section | PASS | strict-XFAIL | PENDING | Resolving phase |
|---|---|---|---|---:|---:|---:|---|
| C1-R2.1 | `tests/capability/test_c1_rev2_contract_objects.py` | C-08 / C-12 object model | REV2 §§5-7; C-08; C-12 §§2,7,8 | 1 | 8 | 0 | R2-P1 / R2-P7 |
| C1-R2.2 | `tests/runtime/test_c1_rev2_cognitive_boundary.py` | C-00 semantic authority; C-08 provider execution only | REV2 §§8-9; C-00 | 2 | 6 | 1 | R2-P4; D-01 audit |
| C1-R2.3 | `tests/runtime/test_c1_rev2_context_os_projection.py` | C-03 model-visible Context OS gateway; C-08/C-12 projection separation | REV2 §§10,15; C-03 | 4 | 4 | 0 | R2-P1 / R2-P2 / R2-P4 |
| C1-R2.4a | `tests/capability/test_c1_rev2_provider_resolution.py` | C-08 provider mapping exactness; no implicit fallback | REV2 §12.5 | 3 | 2 | 0 | R2-P3 |
| C1-R2.4b | `tests/capability/test_c1_rev2_filesystem_security.py` | canonical filesystem authorization; negative traversal/symlink gate | REV2 §12.5 | 2 | 5 | 0 | R2-P3 |
| C1-R2.5 | `tests/capability/test_c1_rev2_authorization_and_result_semantics.py` | C-08 AuthorizationDecision and result semantics separation | REV2 §13; C-08 | 4 | 5 | 0 | R2-P1 / R2-P2 |
| C1-R2.6 | `tests/runtime/test_c1_rev2_sync_stream_authority.py` | sync/stream authority parity; provider protocol unknowns pending | REV2 §§15,17 | 3 | 2 | 1 | R2-P4 / D-01 / D-03 |
| C1-R2.7 | `tests/capability/test_c1_rev2_ai_theme_degradation.py` | ai_theme failure/degradation semantics; no failure→empty success | REV2 §§18-19; C-12 | 3 | 5 | 0 | R2-P6 + AT-R1/AT-R3 |
| C1-R2.8 | `tests/runtime/test_c1_rev2_action_trace_semantics.py` | C-12 Action / Trace separation | REV2 §§14-15; C-12 §§5-8,15-16 | 4 | 5 | 0 | R2-P7 |
| C1-R2.9 | `tests/runtime/test_c1_rev2_legacy_reachability_contract.py` | legacy/provider reachability classification; unknown facts pending | REV2 §§16-17 | 3 | 1 | 4 | D-01/D-02/D-03/D-04 |

Total C1 REV2 files only:

```text
29 passed, 6 skipped(PENDING), 43 xfailed
```

C1 focused regression including legacy M0/M2 guards:

```text
72 passed, 6 skipped(PENDING), 43 xfailed
```

## 5. Exact Regression Command

Executed from clean worktree:

```text
/Users/admin/julia_core_c1_final_clean
```

Command:

```bash
/opt/miniconda3/bin/python -m pytest \
  tests/capability/test_m0_acceptance.py \
  tests/capability/test_m2_market_brief.py \
  tests/capability/test_c1_rev2_contract_objects.py \
  tests/runtime/test_c1_rev2_cognitive_boundary.py \
  tests/runtime/test_c1_rev2_context_os_projection.py \
  tests/capability/test_c1_rev2_provider_resolution.py \
  tests/capability/test_c1_rev2_filesystem_security.py \
  tests/capability/test_c1_rev2_authorization_and_result_semantics.py \
  tests/runtime/test_c1_rev2_sync_stream_authority.py \
  tests/capability/test_c1_rev2_ai_theme_degradation.py \
  tests/runtime/test_c1_rev2_action_trace_semantics.py \
  tests/runtime/test_c1_rev2_legacy_reachability_contract.py \
  -q
```

Result:

```text
72 passed, 6 skipped, 43 xfailed
```

## 6. XFAIL Audit

Audit result:

```text
xfail markers inspected: 30
expanded xfailed test cases: 43
strict=True violations: 0
D-01/D-02/D-03/D-04 unknown facts remaining as xfail: 0
```

All xfail markers satisfy:

- `strict=True`
- known implementation gap exists in source or schema
- protected contract is named
- resolving phase is included in reason or file header

## 7. PENDING Audit

PENDING / skipped dispositions are intentionally used where source evidence does not exist.

| Pending ID | Meaning | Current disposition |
|---|---|---|
| D-01 | active production LLM provider source audit | PENDING |
| D-02 | classified legacy/provider reachability kill map | PENDING |
| D-03 | streaming provider protocol mechanics | PENDING |
| D-04 | ai_theme deployment/reachability handoff | PENDING |

No PENDING item may be converted to PASS without evidence. No PENDING item may be converted to XFAIL merely because implementation is missing.

## 8. Gap Register

| Gap | Evidence | Contract | Resolving phase |
|---|---|---|---|
| C-08 object model not converged | legacy `CapabilityRequest` / `CapabilityResult` fields | C-08 / C-12 | R2-P1 |
| AuthorizationDecision not first-class | `PermissionPolicy.check()` returns `(bool, reason)` | C-08 | R2-P1/R2-P2 |
| ToolResult/Evidence/Trace not fully separated | legacy result carries data/evidence together | C-08 / C-12 | R2-P1/R2-P7 |
| Runtime semantic pre-routing | `RuntimeCapabilityBridge.requires_tool()` keyword tables | C-00 / C-08 | R2-P4 |
| WorkflowRouter semantic intent authority | `WorkflowRouter` owns `MarketBriefIntentResolver` | C-00 | R2-P4 |
| Context OS projection accepts flattened string | `project_tool_result(tool_result: str)` | C-03 / C-08 / C-12 | R2-P1/R2-P2 |
| forced retry prompt bypass | `_chat_impl()` appends `[系统提示]` directly | C-03 | R2-P2/R2-P4 |
| capability_bridge prompt fence | `_format_tool_result()` returns fenced `tool_result` text | C-03 / C-08 | R2-P1/R2-P2 |
| local provider mapping defect | provider namespace mismatch | C-08 | R2-P3 |
| filesystem canonical authorization gap | lexical startswith / list/search gaps | REV2 §12.5 | R2-P3 |
| stream capability lifecycle missing | `process_stream()` streams provider deltas directly | C-08 parity | R2-P4 |
| ai_theme failure collapse | mapper swallows source exceptions | REV2 §18 / C-12 | R2-P6 + AT-R3 |
| C-12 Action absent | `runtime/action.py` is operational progress | C-12 | R2-P7 |
| C-12 Trace graph absent | `event_trace.py` is debug timeline | C-12 | R2-P7 |

## 9. REV1 / 773feb5 Disposition

```text
REV1 C1 Schema:
SUPERSEDED
NOT AUTHORITATIVE
NOT USED AS C1 REV2 CONTRACT
```

```text
773feb5:
HISTORICAL PRIOR ATTEMPT
HOLD
DO NOT EXTEND
NOT INCLUDED IN ACTIVE C1 REV2 LINEAGE
```

## 10. Dirty Workspace Exclusion

At C1-FINAL start, current working tree still had unrelated/uncommitted files, including production files such as:

```text
julia_core/capability/market_evidence_formatter.py
julia_core/capability/providers/ai_theme/__init__.py
julia_core/capability/providers/ai_theme/adapter.py
julia_core/context_os/providers/market_context.py
julia_core/runtime/capability_bridge.py
```

These were not used as evidence, were not staged, and were not committed into C1 branch history.

Clean worktree validation was used for regression evidence.

## 11. C1 Freeze / Hold Recommendation

Recommendation:

```text
C1 REV2 BASELINE FREEZE CANDIDATE: READY FOR FINAL FREEZE GATE ✅
PRODUCTION MUTATION: HOLD ✅
R2-P1 PRODUCTION PHASE: DO NOT START UNTIL OWNER APPROVAL ✅
```

Rationale:

- C1 contract safety net is complete for REV2 feature freeze scope.
- Known implementation gaps are protected by strict xfail.
- Unknown provider/reachability/deployment facts are PENDING, not xfail.
- Branch history is docs/tests only.
- No production files entered the active C1 branch lineage.

## 12. Final Gate Statement

C1 establishes executable guardrails. It does not fix production migration debt.

Next allowed action after owner approval:

```text
C1 FINAL FREEZE
```

Not yet allowed:

```text
R2-P1 production mutation
Cognitive executor extraction
provider mapping repair
filesystem security repair
streaming migration
ai_theme live integration
```
