# RD1 C2 Julia Preliminary Research Judgment Implementation Report

## 1. Exact base / ancestry

- Repository: `tonychang925-dev/Julia_core`
- Frozen canonical base: `e2edba9dfff460e3769f93b58491afaf644e6da5`
- Required C1 state: `ac25125045f0997da69693e19581eebf544764cd`
- C2 branch starts at the exact C1 commit; ancestry was verified with `git merge-base --is-ancestor ac25125045f0997da69693e19581eebf544764cd HEAD`.
- No Market, Claude bridge, Assistant, M1B, or frozen C1 verification code is changed.

## 2. Existing cognition path reused

C2 reuses the already-proven Julia cognition spine:

1. Production cognition owner: `JuliaSession`
2. Context authority: `ContextExecutionRuntime`
3. Request/context object: `CognitiveContextPackage`
4. Model boundary: the existing `self.provider.chat(...)`
5. Research-specific parser: `ResearchJudgmentParser`

The new `JuliaSession.form_preliminary_research_judgment()` method projects one C2 unit into `ContextExecutionRuntime`, renders the package with the existing `to_messages()` boundary, invokes the existing model provider, and fail-closes unless that provider emits the exact C2 JSON structure. C2 owns no transport, gateway, loop, retry, fallback, or second runtime.

## 3. C2 architecture

The narrow architecture is:

```text
MarketEventContext
+ NormalizedResearchEnrichment
    ↓ ResearchJudgmentContextBuilder
    ↓ ContextExecutionRuntime.project_research_judgment()
    ↓ existing Julia provider.chat()
    ↓ ResearchJudgmentParser
    ↓ PreliminaryResearchJudgment
```

`ResearchJudgmentContextBuilder` validates the frozen Market contract, rejects unsafe research input, and projects separated situation/evidence/control/capability frames. `ResearchJudgmentParser` is the sole admission gate for Julia-owned structured judgment output.

## 4. Input contracts

C2 consumes only:

- `MarketEventContext`
- `NormalizedResearchEnrichment`

`NormalizedResearchEnrichment` continues to carry `semantic_result`, `observation`, and `tool_result`. Raw D1 JSON never reaches C2. Provider verification labels remain non-authoritative text. Verification state is read only from C1-minted `Evidence.integrity_metadata`.

## 5. PreliminaryResearchJudgment contract

Version: `research.preliminary_judgment.v1`

The domain-specific output retains:

- `judgment_summary`
- `key_drivers`
- `supporting_claims`
- `contradictions`
- `uncertainties`
- `market_implications`
- `confidence`
- `evidence_refs`
- `source_record_refs`
- `reasoning_limits`
- `confidence_basis`
- complete `trace`

Confidence is Julia-owned, finite `[0, 1]`, policy-capped by observation availability, contradictions, unknowns, and verification states. It is never copied from Market, provider, or source confidence.

## 6. Truth-plane handling

The context and output preserve four distinct planes:

- canonical Market event/context;
- provider semantic material;
- runtime source observation evidence;
- Julia's own preliminary inference.

Provider output is explicitly marked research material. Source observations are evidence, not instructions. `SOURCE_VERIFIED` is presented only as runtime content binding, never objective truth. Julia may retain associations without forcing causal certainty.

## 7. Evidence admission policy

- `SOURCE_VERIFIED`: may support `SOURCE_VERIFIED_SUPPORT`; still preliminary and not objective truth.
- `REPORT_ONLY`: may support only `REPORT_ONLY_LEAD`; never verified factual foundation.
- `NOT_PROVEN`: remains visible uncertainty and cannot support strong certainty.
- `BLOCKED`: remains failure/absence truth and a mandatory reasoning limitation.

Driver support labels are checked against the actual C1 evidence states. A model cannot relabel report-only, unproven, unavailable, or blocked material as verified support.

## 8. D1 no-model-synthesis handling

C2 supports the current D1 V1 shape:

```text
factual_summary = ""
claims = []
contradictions = []
unknowns = ["NO_MODEL_SYNTHESIS: ..."]
```

Julia may still form a low-confidence, Market-aware preliminary judgment from canonical Market context, observation/failure truth, and explicit unknowns. C2 never converts observed bytes into synthetic provider claims. Provider contradictions and unknowns omitted by the model are preserved by the parser.

## 9. Provenance / traceability

Every accepted judgment carries a distinct Julia judgment/generation identity plus:

- `market_event_id`
- `source_trace_id`
- `capability_request_id`
- `capability_call_id`
- `correlation_id`
- `tool_result_identity`
- `evidence_refs`
- `source_record_refs`

Evidence and observation provenance must agree on capability request/call and correlation identities. Provider IDs are not reused as Julia cognition IDs.

## 10. Failure / degradation semantics

- Invalid Market context: STOP before cognition.
- Enrichment is not `NormalizedResearchEnrichment`: STOP.
- Provider execution failed: STOP by default; market-only degradation requires an explicit policy flag and preserves failure/limits.
- Observation unavailable: judgment is capped low and explicitly uncertain; verified support is rejected.
- Contradictions/unknowns: preserved and confidence-capped.
- Cognition provider unavailable: the existing provider failure propagates; no alternate cognition stack or fallback.
- Malformed JSON/schema: explicit parse failure; no free-text promotion.
- Trace mismatch: explicit input rejection.

## 11. Trading-prohibition enforcement

Structured parsing recursively rejects forbidden trading fields and rejects trading instruction language in judgment text. Prohibited output fails closed and is not sanitized into a recommendation. No C2 output field or model invocation mode introduces trading semantics.

## 12. Test matrix

Focused regressions cover:

- Positive: C2-P01 through C2-P05
- Negative: C2-N01 through C2-N15
- Context projection through the existing JuliaSession/provider path
- Invalid Market, absent enrichment, provider failure, market-only degradation, and cognition-provider unavailable behavior

Verification commands:

```text
python3.13 -m pytest tests/research/test_c2_preliminary_research_judgment.py -q
  → 24 passed

python3.13 -m pytest tests/research/test_c2_preliminary_research_judgment.py tests/research/test_c1_research_event_enrichment.py tests/capability/test_c1_rev2_authorization_and_result_semantics.py tests/capability/test_r2_p1b_manager_canonical_lifecycle.py tests/runtime/test_c1_rev2_context_os_projection.py tests/runtime/test_c1_rev2_cognitive_boundary.py tests/runtime/test_no_fallback_hardening.py tests/review/test_review_invocation.py tests/review/test_review_sabotage.py -q
  → 212 passed, 1 skipped, 9 xfailed

python3.13 -m compileall -q julia_core/research/judgment.py julia_core/research/__init__.py julia_core/runtime/context_execution_runtime.py julia_core/runtime/julia_session.py tests/research/test_c2_preliminary_research_judgment.py
  → exit 0

git diff --check
  → exit 0
```

## 13. Production files changed

- `julia_core/research/judgment.py`
- `julia_core/research/__init__.py`
- `julia_core/runtime/context_execution_runtime.py`
- `julia_core/runtime/julia_session.py`
- `tests/research/test_c2_preliminary_research_judgment.py`
- `RD1_C2_JULIA_PRELIMINARY_RESEARCH_JUDGMENT_IMPLEMENTATION_REPORT.md`

## 14. Not proven / deferred

- No live external research call.
- No live Claude bridge invocation.
- No B1/B2 Assistant composition.
- No multi-event routing or ranking.
- No fixture E2E.
- No change to C1 verification authority.
- No persisted judgment storage; C2 returns the structured judgment to its caller.

## 15. Architecture deviations

- NONE

## 16. Final verdict

```text
C2 = PASS
```

Remote auditability is established by the ordinary fast-forward feature branch containing this implementation commit; exact branch and HEAD SHA are returned in the C2 status block.
