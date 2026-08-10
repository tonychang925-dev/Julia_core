# Batch I-A — AT-01~AT-17 Offline / Runtime Acceptance Matrix

Status: I-A CLOSED; current runtime state superseded by BATCH_I_RUNTIME_EVIDENCE_UPDATE.md.
Date: 2026-08-10
Mode: Acceptance / verification only. Production behavior changes remain HOLD.

## Gate Rules

- `OFFLINE_PASS` is not `FULL_PASS`.
- Mock/static proof is not runtime behavioral proof.
- GPU/Core runtime-dependent checks remain `RUNTIME_REQUIRED`.
- Codex may create acceptance tests, fixtures, audit/evidence docs, and non-production verification scripts.
- Codex must not patch production behavior, modify frozen contracts, or alter Core/Voice implementation to make tests pass.

## Machine-readable Matrix

Canonical machine-readable matrix:

```text
docs/acceptance/batch_i_a_acceptance_matrix.json
```

## Status Summary

| Range | Offline result | Runtime result | Final status |
|---|---:|---:|---:|
| AT-01~AT-12 | OFFLINE_PASS evidence mapped | RUNTIME_REQUIRED | RUNTIME_REQUIRED |
| AT-13~AT-17 | fixtures/specs frozen | RUNTIME_REQUIRED | RUNTIME_REQUIRED |

No AT is marked `FULL_PASS` in Batch I-A.

## AT Matrix Overview

| AT | Claim | Key contracts | Offline component | Runtime component | GPU | Voice | Cross-provider | Current final status |
|---|---|---|---|---|---|---|---|---|
| AT-01 | Cognitive Boundary | C-00/C-01/C-07 | Runtime not final-answer authority | live provider-origin proof | No | No | No | RUNTIME_REQUIRED |
| AT-02 | Runtime Replacement Prohibition | C-00/C-01/C-03/C-07 | no deterministic replacement authority | live trace | No | No | No | RUNTIME_REQUIRED |
| AT-03 | Context Single Gateway | C-03/C-08/C-09/C-12 | bypass count/source contract | provider-visible provenance | No | No | No | RUNTIME_REQUIRED |
| AT-04 | No Flat Bootstrap | C-03/C-04/C-05/C-08/C-09 | frames/ActiveTail evidence | live package topology | No | No | No | RUNTIME_REQUIRED |
| AT-05 | Conversation Canonicality | C-02/C-03 | transcript authority separation | destructive reconstruction | No | No | No | RUNTIME_REQUIRED |
| AT-06 | Memory Separation | C-02/C-05 | source-ref separation | live memory retrieval | No | No | No | RUNTIME_REQUIRED |
| AT-07 | Continuity Independence | C-03/C-06 | checkpoint/package separation | reconstruct after deletion | No | No | No | RUNTIME_REQUIRED |
| AT-08 | Provider Switch | C-06/C-07 | provider session ephemeral | provider switch run | Yes | No | Yes | RUNTIME_REQUIRED |
| AT-09 | Tool Agency | C-08/C-12/C-03 | ToolResult reinjection path | live tool continuation | No | No | No | RUNTIME_REQUIRED |
| AT-10 | Voice Parity | C-10/C-11/C-03 | voice is transport/body | live Voice/S2S context | No | Yes | No | RUNTIME_REQUIRED |
| AT-11 | Context Budget | C-03/C-09 | budget/topology contract | live budget pressure trace | No | No | No | RUNTIME_REQUIRED |
| AT-12 | Narrative Continuity | C-05/C-02/C-03 | NarrativeExperience structure | live retrieval quality | No | No | No | RUNTIME_REQUIRED |
| AT-13 | Narrative Causal Integrity | C-03/C-05/C-12 | causal fixture frozen | live causal scoring | Yes | No | No | RUNTIME_REQUIRED |
| AT-14 | Effective Context Density | C-03/C-09/C-12 | benchmark fixture frozen | repeated provider trials | Yes | No | Yes | RUNTIME_REQUIRED |
| AT-15 | Relationship Boundary Calibration | C-04/C-05/C-09/C-12 | scenario suite frozen | live calibration scoring | Yes | No | Yes | RUNTIME_REQUIRED |
| AT-16 | Historical Conversation Recovery | C-02/C-03/C-10 | migration integrity fixture | live restart/reopen cognition | Yes | No | No | RUNTIME_REQUIRED |
| AT-17 | Context Source Completeness | C-03/C-12 | provenance schema coverage | provider payload reconciliation | No | No | No | RUNTIME_REQUIRED |

## Evidence Artifacts

- `docs/acceptance/batch_i_a_acceptance_matrix.json`
- `docs/acceptance/fixtures/AT13_AT17_RUNTIME_FIXTURES.md`
- `docs/acceptance/BATCH_I_A_RUNTIME_BLOCKERS.md`
- `scripts/acceptance/batch_i_a_offline_verify.py`

## Exit Gate for I-A

- [x] AT-01~AT-17 matrix exists.
- [x] Every AT has frozen Contract mapping.
- [x] Every AT has offline/runtime decomposition.
- [x] AT-13~AT-17 fixtures frozen.
- [x] Runtime blocker/dependency list created.
- [x] Offline verification script executed and archived.
- [x] No unclassified offline failure.
- [ ] Provider/model runtime requirements recorded during RA setup.
- [ ] Voice scenarios validated during RA setup.
- [ ] Cross-provider scenarios validated during RA setup.
- [x] Production behavior changes = 0 for Batch I-A docs/scripts scope; pre-existing untracked non-production artifacts remain outside this task.

## Current Verdict

Batch I-A offline verification is CLOSED. Later runtime evidence is tracked in `BATCH_I_RUNTIME_EVIDENCE_UPDATE.md` and in the same machine-readable matrix. The original I-A rule remains true historically: offline proof alone did not authorize FULL_PASS.
