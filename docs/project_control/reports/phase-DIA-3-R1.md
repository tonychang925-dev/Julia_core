# DIA-3 R1.6 Implementation Report — Codex A

## Gate input
- Core base: `33d49032b936b0859b21254dab314cf4947d2367`
- R1.5 reviewed target: `ba36d4f8f367b594d17291922fedac07294d08b8`
- R1.6 owner/provenance: `Codex A = DIA-3 implementation provenance`
- Independent verifier remains held: `Codex B = DIA-3 independent sabotage provenance`

## R1.6 HOLD fix addressed
- `R1.5-X2-ORDER ACTIVITY WINDOW CAUSAL POSITION GAP` closed:
  - Activity event subsequence must be non-empty.
  - `window_start_event_id` must be the first canonical event in `EvidenceBasis`.
  - Event-closed `eligibility_event_id` must be the last canonical event in `EvidenceBasis`.
  - Deterministic timer closure requires no fake closing event.
  - Non-event refs may coexist without defining first/last event semantics.
  - Serialization and all golden vectors remain unchanged.

## R1.5 HOLD fix preserved
- R1.5 causal-closure gap closed:
  - `OpportunityKey` now rejects incompatible `TriggerKind` ↔ `CausalAnchor` variants.
  - Single anchor event must be present as canonical `event:<event_id>` source ref.
  - Quiet last event must be present as canonical `event:<last_event_id>` source ref.
  - Activity window start event must be present in `EvidenceBasis`.
  - Event eligibility boundary event must be present in `EvidenceBasis`.
  - Deterministic timer boundary does not require a fake timer event ref.
  - Wrong anchor/source first-write path is rejected before `create_pending` can persist it.
  - OpportunityKey bytes and all golden vectors remain unchanged.

## R1.4 HOLD fix preserved
- `R1.3-X2 CROSS-FIELD CAUSAL CONSISTENCY GAP` closed:
  - `ReflectionOpportunity` construction now rejects reason evidence outside `source_refs`.
  - At least one reason must match `OpportunityKey.trigger_kind`.
  - `ActivityWindowAnchor` opportunities require `source_refs == evidence_basis.source_refs` with exact canonical order.
  - Contradictory first-write path is rejected before `create_pending` can persist it.
  - OpportunityKey bytes and all golden vectors remain unchanged.

## R1.3 HOLD fix preserved
- `R1.2-P0-01 TEMPORAL POLICY SEMANTICS DRIFT` closed:
  - `TriggerPolicy` now uses `datetime.timedelta` duration semantics: `cooldown`, `window`, `quiet_threshold`.
  - Removed `*_event_count` policy fields.
  - `cooldown >= 0`, `window > 0`, `quiet_threshold > 0`.
  - OpportunityKey golden vectors are intentionally unchanged because identity carries opaque `policy_revision`, not policy parameter values.

## R1.2 HOLD fixes preserved
- `R1.1-P0-01 TRIGGER-REASON AUTHORITY ESCAPE` closed:
  - `TriggerReason` is now `kind: TriggerKind` + `evidence_refs: tuple[TriggerSourceRef, ...]`.
  - Removed arbitrary `reason_code` / `detail` strings.
  - Reasons require non-empty tuple evidence refs, exact `TriggerKind`, and duplicate canonical ref rejection.
- `R1.1-P0-02 CAUSAL IDENTITY OVER-BINDING` closed:
  - `SingleEventAnchor` now contains `event_id` only.
  - `QuietWindowAnchor` now contains `last_event_id` + `quiet_boundary_id` only.
  - `ActivityWindowAnchor` retains `window_start_event_id` + `EligibilityBoundary` + ordered `EvidenceBasis`.
- `R1.1-P0-03 ELIGIBILITY BOUNDARY SHAPE MISMATCH` closed:
  - Added `EventEligibilityBoundary(eligibility_event_id)`.
  - Added `DeterministicTimerEligibilityBoundary(deterministic_activity_boundary_id)`.
  - Boundary variant enters canonical bytes; no arbitrary boundary reason text; no actual timer wake wall-clock.
- P1 hardening closed:
  - `OpportunityKey.schema_version` must equal `CANONICAL_VERSION`.
  - `TriggerPolicy` now exposes frozen temporal knobs: `revision`, `cooldown`, `window`, `quiet_threshold`.
  - `BoundedSchedulingState` now models `cursor`, `active_window`, bounded `recent_dedup`, `pending`, and minimal `delivery_tombstones`; no conversation body.

## Preserved from R1/R1.1
- Closed `TriggerKind` enum with exactly four members.
- Real `OpportunityKey` over `schema_version`, `conversation_id`, `policy_revision`, `trigger_kind`, and typed causal anchor.
- Evidence ordering preserved exactly; `A,B != B,A`.
- SHA-256 + versioned canonical serialization + length-framed UTF-8 + domain separation.
- `triggered_at` remains audit-only and excluded from causal identity / exact-retry equality.
- `ReflectionTriggerStateRepository.create_pending` keeps three-state semantics:
  - absent → create
  - same id + same canonical opportunity → idempotent; preserve first durable audit timestamp
  - same id + different canonical opportunity → fail closed via `TriggerIdentityConflict`

## Validation
Command:

```bash
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_trigger/test_dia3_core_contract.py tests/diary/test_dia1_domain.py tests/diary/test_dia2_repository_protocol.py -q
```

Result:

```text
81 passed in 0.21s
```

Compile check:

```bash
/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/reflection_trigger
```

Result: passed.

## R1.6 Golden vectors (unchanged from R1.2/R1.3/R1.4/R1.5)
- Evidence `(evt_A, evt_B)`: `9cb3cdde6c820e68cea2f8b5293bdcc4d7c94480a751bb115c47034c485d8b10`
- Evidence `(evt_B, evt_A)`: `568f80b8e94623c05637906a7b2a1ae9d66a0546b9161f4d62c592c183a8c49d`
- Single-event OpportunityKey: `ec1cc74bb7c07450714555453cd5943828c47385209c57440a6aaa854d6d4123`
- Activity-window OpportunityKey: `c870ebece165b24c77ec758c7ce48ec6f49a7d46d8a944b5b6c3f9ae24127af3`
- Quiet-window OpportunityKey: `175b8861e8b1d342a3048ff0e16eda56a8f5ce669fe4881f34da97966ef47aa0`
- Timer-boundary activity OpportunityKey: `d382582781ce8ee11519bd5e78b6e1adec9d200336684af992dfa7bd79c324d5`

## Review checklist
- [x] DIA-3 implementation provenance remains Codex A.
- [x] Existing DIA-0～DIA-2 provenance untouched.
- [x] No production persistence adapter added.
- [x] No dependency on diary source refs.
- [x] No semantic reason strings in Core.
- [x] `triggered_at` excluded from identity/equality.
- [x] Golden vectors upgraded to R1.2 OpportunityKey model.
- [x] Repository Port fail-closed semantics covered.
- [x] R0.2 frozen nouns present in public exports.
- [x] TriggerPolicy uses duration semantics, not event-count semantics.
- [x] Cross-field causal consistency rejects contradictory first durable pending writes.
- [x] Kind/anchor/source causal closure rejects wrong first-write paths.
- [x] Activity window start/close causal positions are enforced over event subsequence.
