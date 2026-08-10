# Batch I-A Runtime Blocker / Dependency List

Status: Runtime acceptance not started. GPU/Core remain OFFLINE.
Date: 2026-08-10

## RA-01 — Runtime Commit Provenance

Needs:
- running Core includes expected P2/P8/final acceptance commits;
- health endpoint reachable;
- runtime response exposes or can be tied to commit SHA;
- Brain/Electron/Voice commit SHAs recorded where used.

Evidence:
- health JSON;
- git SHA list;
- process start log.

## RA-02 — Core Text Turn Context OS Path

Needs:
- configured ModelProvider;
- fixed conversation fixture;
- ContextPackage trace;
- canonical Conversation commit and read-back.

Evidence:
- request id / turn id;
- package id;
- provider response id;
- canonical message ids.

## RA-03 — Electron E1 Retry-Success

Needs:
- Electron commit `97a04086...` or later containing E1/E2 patch;
- Core runtime with `_last_package` fix active;
- same `turn_id` retry scenario;
- canonical reconcile.

Expected:
- failed local projection replaced by canonical completed message;
- no duplicate optimistic bubble;
- canonical GET remains authority.

## RA-04 — Voice/S2S Context Authority

Needs:
- Voice/S2S runtime;
- C-11-compliant or compatibility-bridged Voice Context path;
- proof Voice has no independent semantic bootstrap authority.

Evidence:
- Voice turn id;
- conversation id;
- ContextPackage/source trace;
- absence of local instruction authority.

## RA-05 — ToolResult Continuation

Needs:
- deterministic capability/tool fixture;
- provider/model runtime;
- ToolResult -> Context OS -> continuation trace.

Expected:
- no direct provider injection bypass;
- same turn / new generation linkage recorded;
- final answer grounded in evidence.

## RA-06 — Provider-Visible Provenance

Needs:
- provider-visible payload capture;
- ContextPackage/frame/source refs;
- reconciliation script/report.

Expected:
- every semantic block traceable;
- no manual bypass;
- no silent Alignment-side semantic selection.

## RA-07 — Restart/Reopen Reconstruction

Needs:
- canonical conversation fixture;
- derived Context artifact deletion;
- provider session deletion;
- process restart;
- reopen from canonical/governed sources.

Expected:
- canonical transcript preserved;
- Continuity refs preserved where applicable;
- new ContextPackage rebuilt;
- live cognition reflects recovered context.

## Runtime-only AT Portions

- AT-13: Narrative causal quality.
- AT-14: repeated Effective Context Density trials.
- AT-15: relationship boundary calibration behavior.
- AT-16: live historical recovery cognition.
- AT-17: provider-visible payload reconciliation.

## Cross-provider Requirements

Required for:
- AT-08 provider switch;
- AT-14 benchmark comparison if final acceptance requires provider diversity;
- AT-15 calibration stability if final acceptance requires provider diversity.

Do not mark these FULL_PASS until real provider/model runs are recorded.
