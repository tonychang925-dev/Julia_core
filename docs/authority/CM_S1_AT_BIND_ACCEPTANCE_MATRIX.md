# CM-S1 AT-BIND-17/20 Acceptance Matrix v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 1 — A-3 Acceptance Matrix (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: STO-F2 @ `edc0692` · CM-S1C/S1D reviewed protocol authority @ `38adf58`

## Status vocabulary (exclusive, single value per row)

```text
SPEC_FROZEN     acceptance definition is frozen; no evidence yet
IMPLEMENTED     production code exists; behavior not yet proven
PASS            production evidence SHA recorded, acceptance satisfied
BLOCKED         reconciliation/cutover blocked on a discovered issue
NOT_APPLICABLE  semantics not yet in scope (e.g. unimplemented lifecycle)
```

```text
SPEC_FROZEN ≠ PASS       (a frozen definition is not evidence)
IMPLEMENTED ≠ PASS       (code existing is not proof)
```

A row converts to PASS only with a recorded evidence SHA from the S1C/S1D implementation lane.

## AT-BIND-20 — Legacy vs Segmented semantic equivalence

| # | Obligation | Source | Status |
|---|---|---|---|
| 20.1 | snapshot equivalence — conversation-level (id/title/topic/tags/created/updated/summary_status/lifecycle) | S1C §3 | SPEC_FROZEN |
| 20.2 | snapshot equivalence — message-level (id/turn/role/modality/source/content/status/created/ordering) | S1C §3 | SPEC_FROZEN |
| 20.3 | lifecycle N/A rule (no synthetic archive/tombstone) | S1C §3 | SPEC_FROZEN |
| 20.4 | behavioral parity — full protocol surface (12 methods) | S1C §7 | SPEC_FROZEN |
| 20.5 | mismatch taxonomy + atomic classification | S1C §4 | SPEC_FROZEN |
| 20.6 | BUILD→FREEZE→PROVE + frozen source | S1C §2 | SPEC_FROZEN |
| 20.7 | idempotent proof | S1C §6 | SPEC_FROZEN |
| 20.8 | sabotage AT-RECON-01..12 | S1C | SPEC_FROZEN |

**AT-BIND-20 CLOSED** only when all rows 20.1–20.8 → PASS with S1C evidence SHA.

## AT-BIND-20 — 12-method behavioral parity (individual)

```text
lifecycle/query (6):
  get                       SPEC_FROZEN
  list_all                  SPEC_FROZEN
  create_with_id            SPEC_FROZEN
  delete                    SPEC_FROZEN
  update_title              SPEC_FROZEN
  search                    SPEC_FROZEN
canonical-message (2):
  add_message               SPEC_FROZEN
  update_message_status     SPEC_FROZEN
lookup (2):
  find_turn                 SPEC_FROZEN
  get_messages              SPEC_FROZEN
batch (2):
  append_external_turns_atomic   SPEC_FROZEN
  import_messages_atomic         SPEC_FROZEN
```

Each method PASS requires contract-equivalent return shape / identity / ordering / failure mode between LegacyRepository and SegmentedJsonlConversationRepository.

## AT-BIND-17 — Governed repository cutover

| # | Obligation | Source | Status |
|---|---|---|---|
| 17.1 | S1D state machine is the only activation path | S1D §1 | SPEC_FROZEN |
| 17.2 | authority identity vs write availability during freeze | S1D §1 | SPEC_FROZEN |
| 17.3 | CUTOVER_ALLOWED conditions 1..7 | S1D §2 | SPEC_FROZEN |
| 17.4 | staged candidate_adapter_ready (no early rebind) | S1D §2 | SPEC_FROZEN |
| 17.5 | CutoverFreezeBoundary + accepted-turn accounting | S1D §6 | SPEC_FROZEN |
| 17.6 | ACTIVATE single-authority proof | S1D §3 | SPEC_FROZEN |
| 17.7 | RETIRE ≠ delete (legacy bytes survive) | S1D §4 | SPEC_FROZEN |
| 17.8 | rollback losslessness (post-ACTIVATE truth preserved) | S1D §5 | SPEC_FROZEN |
| 17.9 | sabotage AT-CUT-01..12 | S1D | SPEC_FROZEN |

**AT-BIND-17 CLOSED** only when all rows 17.1–17.9 → PASS with S1D evidence SHA.

## Evidence ledger (to be filled by implementation lane)

```text
AT-BIND-20 evidence SHA : (pending CM-S1C implementation)
AT-BIND-17 evidence SHA : (pending CM-S1D implementation)
```

```text
FROZEN definitions here ≠ CLOSED obligations.
CLOSED requires the evidence SHA above.
```

## Document status vocabulary

- FROZEN: matrix accepted and sealed (current).
