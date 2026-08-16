# DIA-3 R1.1 Implementation Report — Codex A

## Gate input
- Core base: `33d49032b936b0859b21254dab314cf4947d2367`
- R1 reviewed target: `ed2da4c79683d2519e71e86ce316c9bfc7b03db2`
- R1.1 owner/provenance: `Codex A = DIA-3 implementation provenance`
- Independent verifier remains held: `Codex B = DIA-3 independent sabotage provenance`

## RED/HOLD fixes addressed
- `R1-P0-01`: Added closed `TriggerKind` enum with exactly:
  - `TURN_BOUNDARY`
  - `QUIET_WINDOW`
  - `ACTIVITY_WINDOW`
  - `EXPLICIT_REFLECTION_REQUEST`
  - arbitrary strings rejected by `OpportunityKey`.
- `R1-P0-02`: Added real `OpportunityKey`; identity now hashes:
  - `schema_version`
  - `conversation_id`
  - `policy_revision`
  - `trigger_kind`
  - typed `causal_anchor`
- `R1-P0-03`: Evidence ordering no longer sorted lexically. `EvidenceBasis.source_refs` is preserved exactly as already-canonical causal event order; `A,B` and `B,A` digest differently.
- Activity-window closure restored through:
  - `ActivityWindowAnchor.window_start_event_id`
  - `EligibilityBoundary`
  - `EvidenceBasis`
- Quiet-window identity restored through:
  - `QuietWindowAnchor.last_event_id`
  - `QuietWindowAnchor.quiet_boundary_id`
  - `EvidenceBasis`
- Added Core nouns:
  - `TriggerReason`
  - `SingleEventAnchor`
  - `ActivityWindowAnchor`
  - `QuietWindowAnchor`
  - `OpportunityKey`
  - `ReflectionOpportunity`
  - `TriggerPolicy`
  - `PendingOpportunity`
  - `BoundedSchedulingState`

## Preserved from R1
- Trigger-owned typed opaque `TriggerSourceRef`.
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
54 passed in 0.25s
```

Compile check:

```bash
/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/reflection_trigger
```

Result: passed.

## R1.1 Golden vectors
- Evidence `(evt_A, evt_B)`: `9cb3cdde6c820e68cea2f8b5293bdcc4d7c94480a751bb115c47034c485d8b10`
- Evidence `(evt_B, evt_A)`: `568f80b8e94623c05637906a7b2a1ae9d66a0546b9161f4d62c592c183a8c49d`
- Single-event OpportunityKey: `75a32cd8d2cfc442417cd9bd44b9c60aa6053f145d81eaa86f611a1f1defd90b`
- Activity-window OpportunityKey: `b47dc1eca890e4b0d8d5f7b634a49a1de83405731fce90f00179b9a35848eb6c`
- Quiet-window OpportunityKey: `97662f903bb5c0e0a3cfeeb265b27f613cb362b6c9ab2b45517bd50958015919`

## Review checklist
- [x] DIA-3 implementation provenance remains Codex A.
- [x] Existing DIA-0～DIA-2 provenance untouched.
- [x] No production persistence adapter added.
- [x] No dependency on diary source refs.
- [x] `triggered_at` excluded from identity/equality.
- [x] Golden vectors upgraded to OpportunityKey model.
- [x] Repository Port fail-closed semantics covered.
- [x] R0.2 frozen nouns present in public exports.
